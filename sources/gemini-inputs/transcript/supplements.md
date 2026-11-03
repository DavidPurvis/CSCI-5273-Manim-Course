# CSCI 5273 Supplement Transcript

Timecodes are positions in the supplements video. Page numbers are 1-based instructor PDF pages.

## Chapter 17: Practice midterm walkthrough

### 17.1 Practice question 1: switch learning

[00:00:00] (lec06-lan.pdf p31) Practice question 1. This walkthrough follows a generated practice midterm, not your instructor's exam, so use it to test your reasoning, not to predict questions. If you haven't tried the test yet, stop now and take it first. A switch starts with an empty table. A is on port 1, B is on port 2, and C is on port 3, all in one VLAN. Trace A to B, then B to A, then C to B. After each frame, give the table change and the output ports.

[00:00:37] (lec06-lan.pdf p31) Work all three frames before going on.

[00:00:57] (lec06-lan.pdf p31) First frame, A to B. The switch reads the source address, so it learns that A is on port 1. Then it looks up the destination. B is unknown, so it floods out ports 2 and 3.

[00:01:14] (lec06-lan.pdf p32) Second frame, B to A. Source first: B is on port 2. Now the destination, A, is in the table, so the frame goes only out port 1.

[00:01:27] (lec06-lan.pdf p34) Third frame, C to B. The source teaches the switch that C is on port 3. B is known, so the frame goes out port 2. The final table is A on 1, B on 2, and C on 3.

[00:01:44] (lec06-lan.pdf p34) The tempting mistake. After the first frame, many people write B into the table, because A mentioned B. But a destination address tells the switch nothing about where B is. Only a frame sent by B can do that.

[00:02:02] (lec06-lan.pdf p34) On marks: three points for the three forwarding actions, and two for source learning with the correct final table.

### 17.2 Practice question 2: collisions and loops

[00:02:11] (lec06-lan.pdf p22) Practice question 2. Explain why full-duplex switching can still queue, and why redundant Ethernet links need spanning tree. Then say which problem each mechanism addresses: collision, output contention, or a flooding loop.

[00:02:29] (lec06-lan.pdf p22) Match each mechanism to its problem before going on.

[00:02:47] (lec06-lan.pdf p23) Full duplex gives each point-to-point link its own send and receive paths, so the shared half-duplex collision contest is gone on that link. But two inputs can still want the same output at the same moment. Only one frame can leave at a time, so the other one queues. There's no collision, just contention.

[00:03:11] (lec06-lan.pdf p35) The loop. Redundant links form a cycle in the active topology. A flooded frame goes around that cycle, and Ethernet has no hop limit to stop it. Spanning tree blocks enough links that the active topology has no cycle, so flooded frames can't circulate forever.

[00:03:32] (lec06-lan.pdf p37) The tempting answer blurs these together. Full duplex does not remove queues, and spanning tree does not prevent collisions. Keep the scopes apart. Full duplex ends the collision contest on a link. Queues handle output contention. Spanning tree handles flooding loops.

[00:03:55] (lec06-lan.pdf p37) On marks: two points for output contention, two for flooding and spanning tree, and one for keeping the scopes separate.

### 17.3 Practice question 3: prefix arithmetic

[00:04:05] (lec07-network1.pdf p23) Practice question 3. For 172.16.5.130/22, give the mask, the network, the broadcast address, and the conventional usable count. Then decide whether 172.16.7.12 is on the same subnet.

[00:04:28] (lec07-network1.pdf p23) Do the arithmetic on paper. Remember to show your work.

[00:04:57] (lec07-network1.pdf p22) A slash 22 means 22 network bits, so the mask is 255.255.252.0. The boundary falls inside the third byte. Six of that byte's bits are network bits and two are host bits, so third-byte blocks have size 4.

[00:05:19] (lec07-network1.pdf p23) The third byte is 5, and 5 lies in the block from 4 through 7. So the network is 172.16.4.0, and the broadcast is 172.16.7.255. That leaves 10 host bits, so 2 to the 10th, minus 2, gives 1,022 usable addresses.

[00:05:45] (lec07-network1.pdf p23) 172.16.7.12. Its third byte is 7, which sits in the same block. So yes, it's on the same subnet, even though 5 and 7 look different.

[00:06:01] (lec07-network1.pdf p23) The tempting answer treats this like a slash 24: network 172.16.5.0, broadcast 172.16.5.255. That ignores the mask. The host part begins inside the third byte, so the block crosses several values of it.

[00:06:25] (lec07-network1.pdf p23) On marks: one point for each requested result.

### 17.4 Practice question 4: fragmentation

[00:06:30] (lec07-network1.pdf p36) Practice question 4. A 2,600 byte IPv4 datagram, with a 20 byte header and no options, may be fragmented over an MTU of 1,000. Give each fragment's payload length, total length, offset, and more fragments flag. Then explain the offset unit.

[00:06:54] (lec07-network1.pdf p37) Work out the whole table on paper.

[00:07:19] (lec07-network1.pdf p37) The data is 2,600 minus 20, which is 2,580 bytes. Each fragment has room for 1,000 minus 20, or 980 bytes of data. But nonfinal payloads must be multiples of 8, so round down to 976.

[00:07:40] (lec07-network1.pdf p37) The payloads are 976, 976, and what's left, 628. Adding 20 byte headers gives total lengths of 996, 996, and 648. The offsets are 0, 122, and 244. The more fragments flags are 1, 1, and 0.

[00:08:09] (lec07-network1.pdf p37) Why 122? The offset field counts in units of 8 bytes of original data, and 976 divided by 8 is 122. It counts position in the data, not headers.

[00:08:25] (lec07-network1.pdf p37) The tempting answer cuts at 980, the space that's available. But then a second fragment would start at byte 980, and that position can't be written as a whole number of 8 byte units.

[00:08:40] (lec07-network1.pdf p37) On marks: one point each for the payload calculation, the totals, the offsets, the flags, and the explanation of the unit.

### 17.5 Practice question 5: longest match

[00:08:51] (lec08-network2.pdf p28) Practice question 5. Installed routes are 10.0.0.0/8 to A, 10.4.0.0/16 to B, 10.4.8.0/21 to C, and slash 0 to D. Choose outputs for 10.4.9.7, 10.4.20.1, 10.8.1.2, and 192.0.2.8. Then explain why a lower-cost slash 8 would not replace a matching slash 21 during ordinary lookup.

[00:09:30] (lec08-network2.pdf p28) Choose all four outputs before going on.

[00:09:55] (lec08-network2.pdf p29) Start with 10.4.9.7. It's inside the slash 8, and inside the slash 16. For the slash 21, third-byte blocks have size 8, and 9 lies in 8 through 15. So it matches that too, and the longest wins: output C.

[00:10:16] (lec08-network2.pdf p29) 10.4.20.1 matches the slash 8 and the slash 16. Its third byte, 20, is outside 8 through 15, so the slash 21 doesn't match. Output B. 10.8.1.2 matches only the slash 8 and the default. Output A. And 192.0.2.8 matches only the default: output D.

[00:10:45] (lec08-network2.pdf p29) Why doesn't cost matter? Cost belongs to route selection, which happens before a prefix is installed. Forwarding among installed matches uses prefix length alone. So a matching slash 21 beats a slash 8, however cheap the slash 8 looks.

[00:11:06] (lec08-network2.pdf p29) The tempting answer lets the cheaper route win, or takes whichever route is listed first. Neither one affects an ordinary lookup.

[00:11:17] (lec08-network2.pdf p29) On marks: four points for the outputs, and one for the distinction.

### 17.6 Practice question 6: queues

[00:11:23] (lec08-network2.pdf p24) Practice question 6. Input FIFO X holds two packets: first, one for output 1, then one for output 2. Another input wins output 1, while output 2 sits idle. Name and explain the problem. Then, does a faster fabric fix sustained 20 megabits per second of demand on a 10 megabit per second output?

[00:11:51] (lec08-network2.pdf p24) Name the problem, and decide about the faster fabric.

[00:12:09] (lec08-network2.pdf p24) The problem is head of line blocking. X's first packet can't use output 1 during this slot. The packet behind it wants output 2, which is free. But a first-in, first-out queue won't let it pass.

[00:12:26] (lec08-network2.pdf p25) The overload. 20 megabits per second arrive, and the output sends only 10. So the backlog grows at 10 megabits per second, for as long as that lasts. A faster fabric only delivers packets to that same output sooner. The output link's rate is the limit.

[00:12:47] (lec08-network2.pdf p25) The tempting fix is a faster fabric, or a bigger buffer. A bigger buffer absorbs a burst, but under sustained overload it only adds delay before the same drops.

[00:13:01] (lec08-network2.pdf p25) On marks: three points for the head of line mechanism, and two for the overload reasoning.

### 17.7 Practice question 7: the bootstrap trace

[00:13:08] (lec09-discovery.pdf p54) Practice question 7. DHCP confirms a client at 192.0.2.10/24, gateway 192.0.2.1, and DNS server 198.51.100.53. The client wants www.example.test, and all caches are empty. Outline the DHCP message order, which IP address is ARPed before the DNS query leaves, and the Ethernet and IP destinations of that query. Then explain why "DNS always happens before ARP" is misleading.

[00:13:52] (lec09-discovery.pdf p54) Write the order down before going on.

[00:14:12] (lec09-discovery.pdf p22) DHCP goes Discover, Offer, Request, ACK.

[00:14:19] (lec09-discovery.pdf p24) The DNS server. 198.51.100.53 is off-link. Under a slash 24, it isn't in 192.0.2. So the client must send through its gateway, and it ARPs for the gateway, 192.0.2.1.

[00:14:43] (lec09-discovery.pdf p58) The query then leaves with the gateway's MAC as its Ethernet destination, and the DNS server, 198.51.100.53, as its IP destination.

[00:14:58] (lec09-discovery.pdf p54) Why is "DNS always happens before ARP" misleading? Because conceptually you want the name first, but the DNS query is itself a packet. It can't leave until its local delivery dependency is met. Request order isn't packet transmission order.

[00:15:18] (lec09-discovery.pdf p54) On marks: one point per statement.

### 17.8 Practice question 8: directory roles

[00:15:23] (lec09-discovery.pdf p41) Practice question 8. A resolver receives an NS referral, then a CNAME, then an A record. Explain each value's role. Distinguish the client's recursive request from the resolver's iterative queries, and give one cache-freshness tradeoff.

[00:15:43] (lec09-discovery.pdf p41) Give the three roles and the distinction before going on.

[00:16:02] (lec09-discovery.pdf p42) An NS record names an authoritative server for a zone. It's a delegation, telling the resolver whom to ask next. A CNAME gives an alias's target hostname, so the resolver goes on to look up that name. And an A record finally supplies an IPv4 address.

[00:16:26] (lec09-discovery.pdf p35) Recursive means, obtain it for me. That's the client's request to its resolver. Iterative means, answer or tell me whom to ask. That's how the resolver queries the hierarchy.

[00:16:42] (lec09-discovery.pdf p37) The tradeoff: a long TTL reduces work and latency, but it delays noticing changes.

[00:16:50] (lec09-discovery.pdf p42) The tempting mistake treats every record as an address. NS and CNAME both give host names. Only the A record gives the address.

[00:17:02] (lec09-discovery.pdf p42) On marks: one point for each of the three record roles, one for the query distinction, and one for the tradeoff.

### 17.9 Practice question 9: Dijkstra

[00:17:11] (lec10-routing.pdf p27) Practice question 9. Undirected edges are A B 2, A C 6, B C 1, B D 5, and C D 2. Compute distances from A to B, C, and D. Give D's predecessor, and A's first hop toward D. State the ordinary edge-weight condition.

[00:17:34] (lec10-routing.pdf p27) Run it on paper. Keep distances, predecessors, and first hops separate.

[00:18:02] (lec10-routing.pdf p28) Settle A. Tentative distances are B 2, C 6, and D infinity. Settle B at 2. Through B, C costs 3, which beats 6, and D costs 7. Settle C at 3. Through C, D costs 5, which beats 7. Settle D at 5.

[00:18:26] (lec10-routing.pdf p36) The distances are 2, 3, and 5. D's predecessor is C. But A's first hop toward D is B, since the path is A, B, C, D. And Dijkstra assumes nonnegative edge weights.

[00:18:44] (lec10-routing.pdf p36) The tempting mistake: D's predecessor is C, so A must send to C. No. The predecessor is the node just before D on the path. The first hop is the neighbor just after A.

[00:18:59] (lec10-routing.pdf p36) On marks: two points for final distances, one for the predecessor, one for the first hop, and one for the condition.

### 17.10 Practice question 10: Bellman-Ford

[00:19:10] (lec10-routing.pdf p40) Practice question 10. X reaches neighbor V with cost 2, and neighbor W with cost 4. V advertises distance 7 to Z, and W advertises 2. Compute X's distance and next hop. If W later advertises 9 instead, recompute. And state what X trusts from its neighbors.

[00:19:36] (lec10-routing.pdf p40) Do both updates before going on.

[00:19:56] (lec10-routing.pdf p41) Through V: 2 plus 7 is 9. Through W: 4 plus 2 is 6. The minimum is 6, so the next hop is W.

[00:20:09] (lec10-routing.pdf p41) W says 9. Through W, 4 plus 9 is 13. V still gives 9. So X's distance becomes 9, through V.

[00:20:23] (lec10-routing.pdf p39) X trusts its neighbors' currently advertised remaining distances, and those may be stale. It doesn't see the paths behind them.

[00:20:33] (lec10-routing.pdf p39) The tempting shortcut looks only at link costs: 2 beats 4, so choose V. But the total decides, and W's total was the smaller one at first.

[00:20:47] (lec10-routing.pdf p39) On marks: two points for each correct update and next hop, and one for the information distinction.

### 17.11 Practice question 11: bad news

[00:20:55] (lec11-convergence.pdf p16) Practice question 11. X to Y costs 1, and Y to Z costs 1, with no other path to X. At first, Y reaches X directly, and Z uses Y. Then the link from X to Y fails. Show one circular stale-distance sequence. Explain exactly what Z advertises to Y under poison reverse, and give one limit of that technique.

[00:21:24] (lec11-convergence.pdf p16) Write out the sequence, and the exact advertisement.

[00:21:46] (lec11-convergence.pdf p17) Z's old 2 leads Y to claim 3, through Z. Y's 3 leads Z to claim 4, through Y. Then Y can claim 5, and so on. No real path exists. The two routers are feeding each other.

[00:22:03] (lec11-convergence.pdf p18) Under poison reverse, Z uses Y to reach X, so Z tells Y that its distance to X is infinity. That advertisement is specific to Y. Z's route is unchanged, and other neighbors can still hear the truth.

[00:22:21] (lec11-convergence.pdf p18) The limit: it doesn't eliminate every longer dependency cycle. With three or more routers in a loop, the counting can still happen.

[00:22:32] (lec11-convergence.pdf p18) The tempting answer says Z deletes its route, or tells everyone infinity. It doesn't. Z keeps its route, and only Y hears the infinity.

[00:22:45] (lec11-convergence.pdf p18) On marks: two points for the circular trace, two for the exact poisoned direction and value, and one for a limitation.

### 17.12 Practice question 12: stability

[00:22:55] (lec11-convergence.pdf p7) Practice question 12. Name the four convergence stages. Explain why path-vector own-AS rejection does not guarantee rapid convergence, or a stable result under arbitrary policies. Then distinguish exploration from persistent policy oscillation.

[00:23:16] (lec11-convergence.pdf p7) Answer all three parts before going on.

[00:23:33] (lec11-convergence.pdf p7) Detect, disseminate, compute, install.

[00:23:40] (lec11-convergence.pdf p26) Rejecting a path with your own AS number stops one kind of loop. But many loop-free candidate paths may remain, and a router can try them one after another. And nothing forces everyone's preferences to be compatible.

[00:23:59] (lec11-convergence.pdf p29) Exploration is a temporary response to incomplete news about a withdrawal or a change: routers try paths, and settle. Oscillation can persist, because the policy choices have no compatible stable assignment. With no stable answer, there's nothing to settle on.

[00:24:20] (lec11-convergence.pdf p33) The tempting answer says that no loops means stable. But loop-free is a property of each path. Stability is a property of everyone's choices together.

[00:24:33] (lec11-convergence.pdf p33) On marks: two points for all the stages, one for exploration, one for the policy conflict, and one for the distinction.

### 17.13 Practice question 13: BGP selection

[00:24:43] (lec12-bgp.pdf p26) Practice question 13. Route A has local preference 150, AS length 5, and egress cost 20. B has preference 100, length 2, and cost 1. Which wins? If their local preference becomes equal, which wins? And how does the chosen BGP next hop become a usable local forwarding action?

[00:25:11] (lec12-bgp.pdf p26) Choose both winners, and explain the next hop.

[00:25:28] (lec12-bgp.pdf p26) Local preference comes first. 150 beats 100, so A wins, and its longer path never matters.

[00:25:39] (lec12-bgp.pdf p26) Make the preferences equal. Now AS length decides. B's 2 beats A's 5, so B wins, before egress cost is ever compared.

[00:25:52] (lec12-bgp.pdf p28) The next hop. BGP's chosen next hop may be several routers away. It must resolve through internal reachability, to a usable output and an adjacent next hop. Only then can it be installed.

[00:26:09] (lec12-bgp.pdf p28) The tempting answer adds the numbers into a score, or picks the lowest cost. BGP doesn't do that. It compares one attribute at a time, and stops as soon as one route remains.

[00:26:24] (lec12-bgp.pdf p28) On marks: two points for the first choice and its reason, one for the second choice, and two for resolution.

### 17.14 Practice question 14: commercial policy

[00:26:33] (lec12-bgp.pdf p41) Practice question 14. Under the lecture model, decide whether a provider-learned route may be exported to a customer, and to a peer. Classify the data paths up, peer, down, and down, up as valid or invalid. Then state the preference and topology conditions that accompany the export restriction in Gao-Rexford.

[00:26:58] (lec12-bgp.pdf p41) Answer each part before going on.

[00:27:17] (lec12-bgp.pdf p41) A provider-learned route to a customer: yes. The customer pays you to reach the world. To a peer: no. That would have you carrying traffic between two non-customers.

[00:27:34] (lec12-bgp.pdf p43) Up, peer, down is valley free, so it's valid. Down, then up is a valley: some customer would be carrying traffic between its providers. That one's invalid.

[00:27:49] (lec12-bgp.pdf p39) Gao-Rexford adds two more conditions. Prefer customer routes over peer and provider routes. And keep the customer-provider hierarchy free of cycles.

[00:28:02] (lec12-bgp.pdf p41) The tempting answer says a peer hears everything. A peer hears only your own routes and your customers' routes.

[00:28:11] (lec12-bgp.pdf p41) On marks: one point for each export answer, one for both path classifications, and one each for the preference and topology conditions.

### 17.15 Practice question 15: audience and bandwidth

[00:28:23] (lec13-multicast.pdf p22) Practice question 15. Distinguish anycast and multicast. A 10 megabit per second stream has three recipients sharing the first link. Compare first-link traffic for iterated unicast and for network multicast, before branching. Then give one anycast failover limitation.

[00:28:46] (lec13-multicast.pdf p22) Work out the two rates, and the distinction.

[00:29:04] (lec13-multicast.pdf p5) Anycast selects one service instance for a shared address. Multicast delivers to the whole interested group.

[00:29:15] (lec13-multicast.pdf p22) Iterated unicast sends three copies over the first link: 3 times 10 is 30 megabits per second. Multicast sends one copy until the branch: 10.

[00:29:28] (lec13-multicast.pdf p14) One limitation: if routing switches a flow to another instance, that instance may lack the connection state. Convergence delay, or application health that routes don't reflect, would also be fair answers.

[00:29:45] (lec13-multicast.pdf p14) The tempting mix-up says anycast reaches a group. It reaches one instance. It's multicast that reaches the group.

[00:29:55] (lec13-multicast.pdf p14) On marks: two points for the audience distinction, two for the rates, and one for a valid limitation.

### 17.16 Practice question 16: membership and trees

[00:30:05] (lec13-multicast.pdf p46) Practice question 16. Explain the roles of IGMP, a receiver DR's star comma G PIM join, and a source DR's Register. Compare the dense and sparse defaults, and describe the purpose of an S comma G switch.

[00:30:23] (lec13-multicast.pdf p46) Give each role before going on.

[00:30:40] (lec13-multicast.pdf p47) IGMP expresses receiver interest on the LAN. The star comma G join builds receiver-side state toward the RP. And Register brings source startup traffic from the source's DR to the RP.

[00:30:56] (lec13-multicast.pdf p50) Dense mode forwards unless pruned. Sparse mode needs joins. An S comma G switch creates a source-rooted path that can avoid the RP detour.

[00:31:09] (lec13-multicast.pdf p50) The tempting mistake says IGMP builds the multicast tree. It doesn't. IGMP works on the LAN, and PIM connects the routers.

[00:31:22] (lec13-multicast.pdf p50) On marks: one point per role or distinction.

### 17.17 Practice question 17: hidden terminals

[00:31:27] (lec14-wireless.pdf p23) Practice question 17. A and C cannot hear each other, but both can transmit to B. Explain why carrier sensing can fail, and how CTS can help. State why no ACK is not proof of collision, and name one cost of RTS and CTS.

[00:31:48] (lec14-wireless.pdf p23) Answer each part before going on.

[00:32:04] (lec14-wireless.pdf p23) A and C each sense local silence, yet their signals interfere at B.

[00:32:11] (lec14-wireless.pdf p24) B's CTS can be heard by C, even though C can't hear A. So C defers.

[00:32:20] (lec14-wireless.pdf p30) A missing ACK can also mean data corruption, or a lost ACK. And RTS and CTS cost control airtime, and those control packets can collide too.

[00:32:33] (lec14-wireless.pdf p26) The tempting answer says that silence at the sender means the channel is safe. What matters is interference at the receiver.

[00:32:43] (lec14-wireless.pdf p26) On marks: two points for geometry and sensing, one for CTS, one for the loss interpretation, and one for the cost.

### 17.18 Practice question 18: CDMA

[00:32:54] (lec14-wireless.pdf p15) Practice question 18. Let c 1 be 1, 1, minus 1, minus 1, and let c 2 be 1, minus 1, 1, minus 1. d 1 is minus 1, and d 2 is plus 1. Compute the summed chip vector z, and recover both bits by correlation. Then state one ideal-model assumption.

[00:33:20] (lec14-wireless.pdf p15) Compute z and both correlations on paper.

[00:33:47] (lec14-wireless.pdf p15) z is minus c 1, plus c 2. Chip by chip, that's 0, minus 2, 2, 0.

[00:33:57] (lec14-wireless.pdf p16) Correlate with c 1: 0, minus 2, minus 2, plus 0 gives minus 4, over 4, which is minus 1. Correlate with c 2: 0, plus 2, plus 2, plus 0 gives plus 4, over 4, which is plus 1.

[00:34:18] (lec14-wireless.pdf p16) One ideal assumption: synchronized orthogonal codes, with suitable power and noise conditions.

[00:34:26] (lec14-wireless.pdf p16) The tempting slips are dividing by 2 instead of the code length, or forgetting that a bit of minus 1 flips the whole code. M here is 4.

[00:34:38] (lec14-wireless.pdf p16) On marks: two points for z, one per decoded bit, and one for the assumption.

### 17.19 Practice question 19: LTE roles

[00:34:46] (lec15-mobile.pdf p13) Practice question 19. Match HSS, MME, S-GW, and P-GW to their roles. Draw the normal UE to Internet user-data path, and explain why the MME need not appear as a payload hop.

[00:35:04] (lec15-mobile.pdf p13) Name each role, and trace the path.

[00:35:22] (lec15-mobile.pdf p14) The HSS holds subscriber profiles and authentication data. The MME handles authentication, mobility, and control setup. The S-GW is the serving user-data and tunnel forwarding point. And the P-GW is the gateway to external packet networks.

[00:35:43] (lec15-mobile.pdf p13) User data goes UE, eNodeB, S-GW, P-GW, Internet. The MME coordinates that path, but control messages aren't payload, so it isn't a hop.

[00:35:58] (lec15-mobile.pdf p14) The tempting mistake sends user data through the MME, because it appears in the diagram's middle. The MME controls the path. The gateways carry the data.

[00:36:11] (lec15-mobile.pdf p14) On marks: one point per component, plus one for the path and control distinction.

### 17.20 Practice question 20: locator and handover

[00:36:19] (lec15-mobile.pdf p34) Practice question 20. A Mobile IP packet's home destination is H, and its care-of locator is C. Name the inner and outer destinations during forwarding through the home agent. Then state the before, during, and after S-GW and base-station data paths, in a handover with old A and target B.

[00:36:43] (lec15-mobile.pdf p34) Answer both parts before going on.

[00:37:01] (lec15-mobile.pdf p34) The inner destination stays H: that's the identity. The outer tunnel destination is C: that's the location.

[00:37:13] (lec15-mobile.pdf p40) Before: S-GW, A, UE. During: S-GW, A, B, UE, through temporary forwarding. After: S-GW, B, UE, once the core endpoint changes.

[00:37:30] (lec15-mobile.pdf p34) The tempting mistake rewrites the inner destination to C. It doesn't change. Only the outer destination carries the location.

[00:37:41] (lec15-mobile.pdf p40) On marks: one point per inner or outer destination, and one per path phase. That's the whole test. For each point you lost, write down the actual cause: wrong scope, wrong table, wrong unit, wrong order, stale dependency, or confused role. Then try a changed example, with new numbers.

## Chapter 18: Exam-day warm-up

### 18.1 The packet story, from memory

[00:38:06] (lec09-discovery.pdf p49) It's Wednesday. Don't reread anything. Get a blank page, and draw the connected packet story from memory, one question at a time. I'll ask, you draw, and then I'll show you the answer. A laptop wakes up, and wants to reach a web server. Start at the very beginning. What does it need before it can send anything?

[00:38:33] (lec09-discovery.pdf p49) Draw the host, the switch, the gateway, the DNS resolver, and the server. Then name what's missing.

[00:38:55] (lec09-discovery.pdf p22) It needs an address, a mask, a gateway, and a resolver. DHCP supplies all four, in four messages: Discover, Offer, Request, ACK.

[00:39:09] (lec09-discovery.pdf p54) The laptop wants the server's name resolved, and the resolver is on another network. What does it send first, and to whom?

[00:39:30] (lec09-discovery.pdf p54) Its mask says the resolver is remote, so the first thing out is an ARP for the gateway. Then the DNS query leaves, with the gateway's MAC on the frame, and the resolver's address in the packet. The frame crosses one link. The packet crosses the network.

[00:39:50] (lec09-discovery.pdf p33) The switch along the way had an empty table. What did it just learn, and what did it do with the frame?

[00:40:09] (lec06-lan.pdf p31) It learned the laptop's port from the source address. If the destination was unknown, it flooded. Once known, it forwards out one port. Source teaches. Destination decides.

[00:40:26] (lec09-discovery.pdf p13) The packet reaches the gateway, headed for the server. What does the router look at, and what changes in the packet?

[00:40:47] (lec08-network2.pdf p13) It reads the destination IP, and picks the longest matching prefix. It replaces the Ethernet frame, and decrements TTL. The source and destination IP addresses stay put.

[00:41:02] (lec09-discovery.pdf p19) Where did that forwarding table come from, inside one network, and between networks?

[00:41:22] (lec10-routing.pdf p37) Inside one AS, link state floods facts and runs Dijkstra, or distance vector trades distances with neighbors. Between ASes, BGP carries paths, shaped by policy and money. The chosen BGP next hop is resolved through internal routing.

[00:41:42] (lec09-discovery.pdf p8) A link fails between the two routers. What goes wrong while the news spreads? Name two failure shapes.

[00:42:03] (lec11-convergence.pdf p8) A blackhole, when a router holds an old route with no working continuation. And a transient loop, when routers install their changes at different times. Detect, disseminate, compute, install. Each stage takes time.

[00:42:23] (lec09-discovery.pdf p39) Last one. The laptop leaves its wire and becomes a moving phone. What stays the same in the packet, and what changes?

[00:42:46] (lec15-mobile.pdf p38) The inner packet stays the same, with its stable address. The outer destination changes, as a tunnel follows the phone. That's the picture from the very start, at a new scale: a local envelope, changing, around a global packet that isn't. If you could draw all of that, you have the story.

### 18.2 One mask, one match, one fragment

[00:43:09] (lec07-network1.pdf p23) A quick recompute, with new numbers, on your own paper. First, a mask. A host has address 192.168.37.200/21. Give the mask, the network, the broadcast address, and the usable count.

[00:43:31] (lec07-network1.pdf p23) Do it from a blank page.

[00:43:52] (lec07-network1.pdf p23) A slash 21 is 255.255.248.0. Third-byte blocks have size 8, and 37 lies in 32 through 39. So the network is 192.168.32.0, and the broadcast is 192.168.39.255. That's 11 host bits, so 2 to the 11th, minus 2, gives 2,046 usable addresses.

[00:44:28] (lec08-network2.pdf p13) A match. A router holds 192.168.0.0/16 to A, 192.168.32.0/21 to B, 192.168.36.0/24 to C, and slash 0 to D. Which output does that same address, 192.168.37.200, use?

[00:45:02] (lec07-network1.pdf p13) Check each prefix, then choose.

[00:45:17] (lec08-network2.pdf p29) It matches the slash 16, the slash 21, and the slash 0. It doesn't match the slash 24, because that covers only third byte 36. So the longest match is the slash 21: output B.

[00:45:35] (lec07-network1.pdf p36) Finally, a fragment. An 1,800 byte datagram, with a 20 byte header, crosses an MTU of 600. Give the largest nonfinal payload, the fragment count, and the offsets.

[00:45:52] (lec07-network1.pdf p37) Round down to a multiple of 8.

[00:46:13] (lec07-network1.pdf p37) 600 minus 20 is 580, and 580 rounds down to 576. The data is 1,780 bytes, so the payloads are 576, 576, 576, and 52. That's four fragments. The offsets go up in steps of 72: 0, 72, 144, and 216. Only the last has its more fragments flag at 0.

### 18.3 Say it out loud

[00:46:49] (lec12-bgp.pdf p24) Recite. Say each answer out loud before I do. First: the BGP selection order, in the lecture's simplified version.

[00:47:01] (lec12-bgp.pdf p24) Go ahead.

[00:47:14] (lec12-bgp.pdf p24) Highest local preference. Then shortest AS path. Then lowest internal cost to the exit. Then a tie break. Compare in order, and stop as soon as one route remains.

[00:47:30] (lec12-bgp.pdf p41) Next: the commercial export rule. Who hears a route learned from a customer? Who hears a route learned from a peer or a provider?

[00:47:51] (lec12-bgp.pdf p41) Own and customer routes go to everyone. Peer and provider routes go only to customers. Would this make me carry traffic between two non-customers? Then don't advertise it. That gives valley-free paths: up, at most one peer link, then down.

[00:48:12] (lec13-multicast.pdf p45) Next: multicast defaults. What does dense mode do by default? And sparse mode?

[00:48:31] (lec13-multicast.pdf p45) Dense mode forwards unless pruned. Sparse mode sends nothing until joined, starting with a shared star comma G tree through the RP, and it may switch to S comma G. IGMP learns local interest, and PIM connects the routers.

[00:48:49] (lec15-mobile.pdf p39) Last: the handover stages. What are the data paths before, during, and after?

[00:49:08] (lec15-mobile.pdf p40) Before: S-GW, A, phone. During: S-GW, A, B, phone, through temporary forwarding. After: S-GW, B, phone. Prepare, move the radio, forward, switch the core path, release.

### 18.4 The slide clarifications

[00:49:29] (lec06-lan.pdf p30) Finally, the places where the slides need a careful reading. These are the corrections and scope notes we met along the way. No new material. For each one, keep the corrected version in mind.

[00:49:45] (lec06-lan.pdf p30) On LANs. The slide's table TTL is a local aging timer in the switch, not a hop count in the frame. And spanning tree, shortest-path trees, and minimum spanning trees have different objectives.

[00:50:02] (lec07-network1.pdf p35) On IP. The maximum IPv4 total length is 65,535 bytes, not the 63,535 printed on the slide, because the field has 16 bits. In the subnet example, 128.101.5.0/23 normalizes to 128.101.4.0/23, and the 31-host department needs a slash 26. And the 51.2 nanosecond budget leaves out Ethernet's physical overhead.

[00:50:42] (lec09-discovery.pdf p31) On discovery. DNS has 13 root identities, A through M, and each is deployed as many physical instances. And the slide's quick TCP recap leaves out the final ACK of the handshake.

[00:50:58] (lec13-multicast.pdf p14) On anycast and multicast. Anycast's problem with TCP is lost connection state, not a blanket incompatibility. IGMP queries go to all hosts, while a report goes to the group being reported. The slide's membership timer computes 270 seconds, while the RFC's default formula gives 260. And sparse mode begins with a shared tree through the RP, whatever the slide's shorthand says.

[00:51:30] (lec14-wireless.pdf p32) On wireless and mobility. Four-address Wi-Fi is a bridging case, not an ad hoc rule. The exposed-terminal shortcut is idealized. IMSI is a decimal subscriber identity of at most 15 digits, not a MAC address. And the foreign-agent drawing is one Mobile IPv4 arrangement, separate from LTE.

[00:51:56] (lec14-wireless.pdf p32) One last thing. A correct answer you can't defend is still a gap, and a mistake you can name is one you won't repeat. Good luck today. You've traced this packet from one wire to a moving phone. Go show them.
