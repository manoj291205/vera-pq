// SPDX-License-Identifier: UNLICENSED
// VERA-PQ course demo. Keep private until a patent application is filed.
pragma solidity ^0.8.24;

/// @notice Hash-only (Keccak-256) audit of a gateway's coordinate-wise trimmed-mean aggregation.
/// No pairings, no ecrecover in the audit path: the soundness of the check rests on hash collision
/// resistance only. Device identity is bound by keccak(ML-DSA public key) in the registry.
/// Crypto-economic layer: a gateway must lock a bond (in ETH) per round. An accepted round releases the
/// bond and pays a reward split between the gateway and the participating IoT devices; a rejected or
/// expired round slashes the bond into the reward pool (with a keeper bounty for whoever calls expire).
/// Payments use a pull pattern (credit + claim) so no external call happens during audit settlement.
contract VeraPQLedger {
    struct Round {
        bytes32 clientRoot;   // Merkle root over (clientId, updateRoot, keccak(mlDsaSig))
        bytes32 aggRoot;      // Merkle root over aggregate coordinates
        uint64 n; uint64 dim; uint32 trim; uint32 k;
        uint64 commitBlock;
        uint8 status;         // 1 committed, 2 accepted, 3 rejected
        address gw;           // gateway whose bond is locked for this round
    }
    struct ClientOpen { uint256 id; bytes32 root; bytes32 sigDigest; bytes32[] path; }
    struct Sample { int256 aggVal; bytes32[] aggPath; int256[] vals; bytes32[][] paths; }

    address public immutable owner;
    mapping(address => bool) public gateway;
    mapping(uint256 => bytes32) public pkHash;   // device id -> keccak(ML-DSA pk)
    mapping(uint256 => uint8) public sigAlg;     // 1 = ML-DSA-44, 2 = ML-DSA-65, ... (crypto-agility hook)
    mapping(uint256 => Round) public rounds;
    uint256 public nextRound = 1;                // round ids are strictly sequential (anti-grinding)

    // ---- crypto-economic layer (all amounts in wei) ----
    uint256 public immutable bond;               // locked per committed round, slashed on reject/expire
    uint256 public immutable roundReward;        // paid from rewardPool on every accepted round
    uint16 public constant GATEWAY_SHARE_BPS = 5000;  // 50% of the reward to the gateway, rest to devices
    uint16 public constant KEEPER_BPS = 1000;          // 10% of a slashed bond to whoever calls expire()
    mapping(address => uint256) public stake;    // deposited by gateways
    mapping(address => uint256) public locked;   // part of stake bonded to unresolved rounds
    mapping(address => uint256) public credit;   // withdrawable balances (pull payments)
    mapping(uint256 => address) public payout;   // device id -> payout address
    uint256 public rewardPool;

    event DeviceRegistered(uint256 indexed id, bytes32 pkHash, uint8 alg);
    event RoundCommitted(uint256 indexed rid, bytes32 clientRoot, bytes32 aggRoot, uint256 n, uint256 dim);
    event RoundAudited(uint256 indexed rid, bool accepted, uint256 failedSample);
    event Staked(address indexed gw, uint256 amount, uint256 total);
    event Rewarded(uint256 indexed rid, address indexed gw, uint256 gatewayAmount, uint256 perDevice);
    event Slashed(uint256 indexed rid, address indexed gw, uint256 amount, address keeper, uint256 bounty);

    constructor(uint256 bond_, uint256 roundReward_) {
        owner = msg.sender; gateway[msg.sender] = true; bond = bond_; roundReward = roundReward_;
    }

    // ---- staking, rewards, withdrawals ----
    function depositStake() external payable {
        stake[msg.sender] += msg.value;
        emit Staked(msg.sender, msg.value, stake[msg.sender]);
    }

    function withdrawStake(uint256 amount) external {
        require(stake[msg.sender] - locked[msg.sender] >= amount, "bonded");
        stake[msg.sender] -= amount;
        credit[msg.sender] += amount;
    }

    function fundRewards() external payable { rewardPool += msg.value; }

    function setPayout(uint256 id, address to) external { require(msg.sender == owner, "owner"); payout[id] = to; }

    function claim() external {
        uint256 amt = credit[msg.sender];
        credit[msg.sender] = 0;                                   // effects before interaction
        (bool ok, ) = msg.sender.call{value: amt}("");
        require(ok, "transfer");
    }

    function setGateway(address g, bool on) external { require(msg.sender == owner, "owner"); gateway[g] = on; }

    function registerDevice(uint256 id, bytes32 h, uint8 alg) external {
        require(msg.sender == owner, "owner");
        pkHash[id] = h; sigAlg[id] = alg;
        emit DeviceRegistered(id, h, alg);
    }

    function commitRound(uint256 rid, bytes32 clientRoot, bytes32 aggRoot, uint64 n, uint64 dim, uint32 trim, uint32 k)
        external
    {
        require(gateway[msg.sender], "gw");
        require(rid == nextRound, "sequence");
        require(rid == 1 || rounds[rid - 1].status >= 2, "previous round unresolved");
        nextRound = rid + 1;
        require(n > 2 * uint64(trim) && dim > 0 && k > 0, "params");
        require(stake[msg.sender] - locked[msg.sender] >= bond, "insufficient stake");
        locked[msg.sender] += bond;
        rounds[rid] = Round(clientRoot, aggRoot, n, dim, trim, k, uint64(block.number), 1, msg.sender);
        emit RoundCommitted(rid, clientRoot, aggRoot, n, dim);
    }

    /// Challenge seed is fixed by the commit block's hash: unknown to the gateway when it committed.
    function challengeSeed(uint256 rid) public view returns (bytes32) {
        Round storage r = rounds[rid];
        require(r.status != 0, "none");
        require(block.number > r.commitBlock && block.number <= r.commitBlock + 256, "window");
        return keccak256(abi.encodePacked(blockhash(r.commitBlock), r.clientRoot, r.aggRoot, rid));
    }

    function audit(uint256 rid, ClientOpen[] calldata cs, Sample[] calldata ss) external returns (bool) {
        Round storage r = rounds[rid];
        require(r.status == 1, "state");
        require(cs.length == r.n && ss.length == r.k, "shape");
        _checkClients(cs, r.clientRoot);
        uint256 failed = _checkSamples(rid, ss, cs);
        bool ok = failed == type(uint256).max;
        r.status = ok ? 2 : 3;
        emit RoundAudited(rid, ok, failed);
        if (ok) _reward(rid, r.gw, cs); else _slash(rid, r.gw, address(0));
        return ok;
    }

    /// A committed round that is not audited inside the blockhash window is rejected (anti-grinding:
    /// the gateway cannot discard an unfavourable challenge and silently retry the same round id).
    function expire(uint256 rid) external {
        Round storage r = rounds[rid];
        require(r.status == 1 && block.number > r.commitBlock + 256, "not expired");
        r.status = 3;
        emit RoundAudited(rid, false, type(uint256).max - 1);
        _slash(rid, r.gw, msg.sender);                            // caller (keeper) earns a bounty
    }

    function _reward(uint256 rid, address gw, ClientOpen[] calldata cs) internal {
        locked[gw] -= bond;
        uint256 pay = roundReward < rewardPool ? roundReward : rewardPool;
        rewardPool -= pay;
        uint256 g = pay * GATEWAY_SHARE_BPS / 10000;
        uint256 each = (pay - g) / cs.length;
        credit[gw] += g;
        for (uint256 i = 0; i < cs.length; i++) {
            address to = payout[cs[i].id];
            if (to == address(0)) rewardPool += each; else credit[to] += each;
        }
        rewardPool += (pay - g) - each * cs.length;               // rounding dust back to the pool
        emit Rewarded(rid, gw, g, each);
    }

    function _slash(uint256 rid, address gw, address keeper) internal {
        locked[gw] -= bond;
        stake[gw] -= bond;
        uint256 bounty = keeper == address(0) ? 0 : bond * KEEPER_BPS / 10000;
        credit[keeper] += bounty;
        rewardPool += bond - bounty;                              // slashed stake funds future honest rounds
        emit Slashed(rid, gw, bond, keeper, bounty);
    }

    function _checkClients(ClientOpen[] calldata cs, bytes32 clientRoot) internal view {
        uint256 dc = _clog2(cs.length);
        for (uint256 i = 0; i < cs.length; i++) {
            if (i > 0) require(cs[i].id > cs[i - 1].id, "order");
            require(pkHash[cs[i].id] != bytes32(0), "unregistered");
            bytes32 leaf = keccak256(abi.encodePacked(cs[i].id, cs[i].root, cs[i].sigDigest));
            require(cs[i].path.length == dc && _verify(leaf, i, cs[i].path, clientRoot), "client path");
        }
    }

    /// @return index of first failing sample, or type(uint256).max if all pass
    function _checkSamples(uint256 rid, Sample[] calldata ss, ClientOpen[] calldata cs) internal view returns (uint256) {
        Round storage r = rounds[rid];
        bytes32 seed = challengeSeed(rid);
        uint256 dd = _clog2(r.dim);
        for (uint256 t = 0; t < ss.length; t++) {
            uint256 j = uint256(keccak256(abi.encodePacked(seed, t))) % r.dim;
            if (!_checkSample(ss[t], cs, j, dd, r.aggRoot, r.trim)) return t;
        }
        return type(uint256).max;
    }

    function _checkSample(Sample calldata s, ClientOpen[] calldata cs, uint256 j, uint256 dd, bytes32 aggRoot, uint32 trim)
        internal pure returns (bool)
    {
        uint256 n = cs.length;
        require(s.vals.length == n && s.paths.length == n, "width");
        for (uint256 i = 0; i < n; i++) {
            bytes32 leaf = keccak256(abi.encodePacked(s.vals[i], j));
            require(s.paths[i].length == dd && _verify(leaf, j, s.paths[i], cs[i].root), "value path");
        }
        require(s.aggPath.length == dd && _verify(keccak256(abi.encodePacked(s.aggVal, j)), j, s.aggPath, aggRoot), "agg path");
        return _trimmedMean(s.vals, trim) == s.aggVal;
    }

    function _trimmedMean(int256[] calldata v, uint32 trim) internal pure returns (int256) {
        int256[] memory a = v;
        for (uint256 i = 1; i < a.length; i++) {          // insertion sort, n is small (gateway cohort)
            int256 key = a[i]; uint256 p = i;
            while (p > 0 && a[p - 1] > key) { a[p] = a[p - 1]; p--; }
            a[p] = key;
        }
        int256 s = 0;
        for (uint256 i = trim; i < a.length - trim; i++) s += a[i];
        return s / int256(a.length - 2 * uint256(trim)); // truncates toward zero (mirrored in Python)
    }

    function _verify(bytes32 leaf, uint256 idx, bytes32[] calldata path, bytes32 root) internal pure returns (bool) {
        bytes32 cur = leaf;
        for (uint256 d = 0; d < path.length; d++) {
            cur = (idx & 1 == 1) ? keccak256(abi.encodePacked(path[d], cur)) : keccak256(abi.encodePacked(cur, path[d]));
            idx >>= 1;
        }
        return cur == root;
    }

    function _clog2(uint256 x) internal pure returns (uint256 d) { while ((uint256(1) << d) < x) d++; }
}
