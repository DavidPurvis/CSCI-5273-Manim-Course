# CSCI 5273 Lectures 6-15: Transcript

Timecodes are positions in the main video. Page numbers are 1-based instructor PDF pages.

## Chapter 6: Lecture 6: LANs and switching

### 6.1 Sharing a wire

[00:00:00] (lec06-lan.pdf p7) Our laptop's very first hop crosses a local network. So start there. Suppose many computers share one wire, and whatever one sends, everybody hears. If two speak at once, the signals garble each other. Who gets to talk, and when? Notice this is not a technical detail. It is a resource allocation problem.

[00:00:23] (lec06-lan.pdf p7) One family of answers is channel partitioning. Divide the wire into fixed shares of time or frequency, one for each user. With four users on a 12 megabit per second wire, each user owns 3 megabits per second. It is perfectly fair and collision free. But watch what happens when only one user has anything to send. Three quarters of the wire sits idle, and that lone user still gets just 3.

[00:00:51] (lec06-lan.pdf p7) A second family is taking turns. A controller polls each station, or a token passes around, so only the holder may send. Idle stations can be skipped, which fixes the waste. The price is control overhead, and a dependency on the coordinator or the token.

[00:01:11] (lec06-lan.pdf p7) The third family is random access. Do not coordinate at all. Whoever has data just tries. When the network is quiet, a lone sender gets nearly the whole wire. When many are active, collisions waste capacity. None of the three wins everywhere. They make different trades among idle capacity, control overhead, and contention. Ethernet chose random access.

[00:01:38] (lec06-lan.pdf p11) Before watching Ethernet contend, look at what it sends. A frame starts with a preamble, which lets the receiver's clock synchronize. Then a destination address, a source address, a type field saying what the payload is, such as IP, then the payload, and finally a CRC that detects corruption. The CRC only detects. It does not repair, and Ethernet sends no acknowledgment. Delivery here is best effort.

[00:02:08] (lec06-lan.pdf p28) Those addresses are MAC addresses, 48 bits burned into each network interface. A MAC address is flat, like a serial number. It says nothing about location, and it has meaning only for local delivery. A network card keeps a frame only if the destination is its own address, or the broadcast address. Everything else, it ignores.

[00:02:32] (lec06-lan.pdf p28) Picture one LAN. A host has one IP address and one MAC address, written as six hexadecimal bytes. A switch learns that MAC from incoming frames. A sending host learns the IP to MAC mapping through ARP. And the broadcast address is all ones.

[00:02:52] (lec06-lan.pdf p12) The Ethernet rule, called CSMA/CD. Carrier sense: listen first, and if someone is talking, wait. Collision detection: keep listening while you send. If what you hear differs from what you sent, there is a collision, so stop and send a brief jam signal. But why would a collision ever happen, if everyone listens first? Because signals take time to travel. A and B can both hear silence, because neither signal has arrived yet.

[00:03:24] (lec06-lan.pdf p12) After a collision, if both retry immediately, they collide again forever. So each picks a random wait. After the m-th collision, choose K from zero up to 2 to the m, minus one, and wait K times 512 bit times. Each further collision doubles the range, so the group spreads itself out without any coordination. That is binary exponential backoff. Try one. After the third collision, K ranges from 0 to 7. On 10 megabit Ethernet, 512 bit times is 51 point 2 microseconds. So K equal to 5 means a wait of 256 microseconds.

[00:04:07] (lec06-lan.pdf p13) There is one more trap. A sender can only detect a collision while it is still transmitting. Suppose A starts at time zero, and the one-way delay is d. B starts just before A's signal arrives, at almost d. B's collision news then needs another d to return. So A may not hear about it until 2 d. So A must still be sending at 2 d, which gives the rule: frame length over rate must be at least twice the propagation delay.

[00:04:37] (lec06-lan.pdf p13) A tempting one: if everyone listens before sending, collisions can't happen. But a signal takes time to travel, so two stations can both hear silence, and both start.

[00:04:50] (lec06-lan.pdf p14) Put in the classic numbers. At 10 megabits per second, with a one-way delay of 25 point 6 microseconds, the frame must last at least 51 point 2 microseconds. That is 512 bits, which is the famous 64 byte minimum Ethernet frame. Now change the delay to just 20 microseconds, at the same rate.

[00:05:14] (lec06-lan.pdf p14) What minimum length does the same formula give now, in bits?

[00:05:31] (lec06-lan.pdf p14) Two times 20 microseconds times 10 megabits per second is 400 bits. That is the formula's answer. It does not replace Ethernet's real minimum of 64 bytes, and the rule belongs to shared, half-duplex wires. Notice what the whole design has been fighting: everyone shares one collision domain. So the next question is obvious. Could we simply stop sharing?

### 6.2 From hub to switch

[00:05:58] (lec06-lan.pdf p15) Plug eight machines into one box. Do they now have eight private conversations, or one big shared one? It depends entirely on what the box does with the bits.

[00:06:11] (lec06-lan.pdf p16) A repeater amplifies a weakening signal, so a LAN can stretch further. A hub is a repeater with many ports. Every bit arriving on one port is copied out of all the others. It reads no addresses. It stores nothing. So a hub with eight ports is still one wire, wearing a different shape. If A sends to B while C sends to D, they collide. The boundary that matters is the collision domain, not the number of boxes in the picture.

[00:06:42] (lec06-lan.pdf p20) Ethernet switching is different in kind. It receives a whole frame, reads the destination MAC address, and sends the frame only out the port that leads there. Now A to B and C to D run at the same time, through independent port pairs, with no collision at all. Each link has become its own little collision domain.

[00:07:05] (lec06-lan.pdf p22) And with a private point to point link, a host can send and receive at once. That is a full-duplex link, and on it, collision detection has nothing left to do. Does that mean a switch never loses anything? No. If A and C both send to B, both frames need the same output. A switch has finite output rates and finite buffers, so frames must queue. We removed collisions, not contention.

[00:07:34] (lec06-lan.pdf p26) One choice remains: when does the switch start sending? Store-and-forward switching receives the entire frame first, and checks the CRC, so bad frames die here. Cut-through switching begins as soon as it has read the destination address. That saves some waiting, but it may forward a frame that later turns out to be corrupt.

[00:07:58] (lec06-lan.pdf p26) It helps to name exactly which delay is being removed. Reception time is frame length divided by rate. A 1500 byte frame at 100 megabits per second takes 120 microseconds just to arrive. Store-and-forward pays this at every switch.

[00:08:16] (lec06-lan.pdf p26) People often say a switch fixes everything a hub got wrong. It doesn't stop broadcasts from spreading, and a collision-free output can still queue and drop.

[00:08:28] (lec06-lan.pdf p26) Change the situation. Our frame's last bytes get corrupted on the way into the switch. And suppose the output port is busy, so the frame cannot begin leaving at once either.

[00:08:41] (lec06-lan.pdf p26) Under cut-through, does the bad frame reach B? And what does cut-through save if the output was busy anyway?

[00:08:55] (lec06-lan.pdf p26) With a free output, cut-through would already be sending when the corruption arrives, so a bad frame can reach B. With a busy output, the frame has to wait anyway, so the savings shrink. Store-and-forward would have discarded it. There is still a gap in the switch story. It sends a frame only out the right port. But how could a box you just took out of the packaging possibly know which port is right?

### 6.3 Learning and loops

[00:09:24] (lec06-lan.pdf p30) Nobody configures a home switch. You plug in the cables and it works. Yet it sends frames out the correct port. Where did that knowledge come from? Pause on a clue: every frame carries two addresses. Only one of them says where a machine actually is right now.

[00:09:43] (lec06-lan.pdf p31) A switch with an empty table, and three hosts. A is on port 1, B is on port 2, and C is on port 3. A sends a frame to B. Watch the order of the next two steps, because they use two different addresses.

[00:10:00] (lec06-lan.pdf p33) First, the switch looks at the source address. This frame says it came from A, and it arrived on port 1. So A must be reachable through port 1. Write that down. Second, it looks up the destination, B. B is not in the table, so the switch has no idea. It floods the frame out every other port. Note what it did not learn. It cannot learn where B is just because A mentioned B.

[00:10:28] (lec06-lan.pdf p34) B answers. Its frame's source address teaches the switch that B is on port 2. And now the destination, A, is in the table, so this frame goes only out port 1. Finally, A sends to B once more. Nothing new to learn. The destination is known, and the frame goes only to port 2. C is no longer bothered.

[00:10:52] (lec06-lan.pdf p30) The rule is, learn from the source, then forward by the destination. Unknown destination, flood. Known destination on another port, forward. Known destination on the arrival port, filter. Entries also expire, so that a host which moves or disappears does not stay wrong forever. The slides call this a TTL. Be careful with that word. It is a local aging timer in the switch. It is not a hop counter carried in the Ethernet frame, and that fact is about to matter a great deal. **Clarification:** The slide's table TTL is a local aging timer, not an Ethernet hop-limit field (lec06 p30).

[00:11:27] (lec06-lan.pdf p35) Networks want spare links, in case one fails. So connect three switches in a triangle. Now send one broadcast. S1 floods it to S2 and S3. Each floods it onward, to the other. Those copies come back, and get flooded again. IP has a TTL that kills looping packets. Ethernet has no such field. The copies circulate and multiply until the network collapses. A cycle in the wiring is fatal.

[00:11:58] (lec06-lan.pdf p37) The fix is the spanning tree protocol. Keep every physical link, but let frames use only a loop-free subset. Switches exchange messages carrying three things: who they think the root is, their distance to it, and their own ID. Each begins by claiming to be the root. Hearing a lower ID, it gives up that claim. **Clarification:** The STP presentation is simplified; real STP needs deterministic ties and designated forwarding (lec06 pp37-40).

[00:12:21] (lec06-lan.pdf p37) Hearing a shorter path to the root, it adopts that path. In the triangle, S1 becomes root, S2 and S3 use their direct links, and the link between them stops forwarding. Three switches, two active links, and no cycle. The slides simplify the real protocol, which also needs deterministic ties and a designated forwarder on each segment.

[00:12:46] (lec06-lan.pdf p41) The exercise from the instructor's slides, with seven switches. The drawing gives no priorities or costs, so we must state an assumption. Treat all links as equal cost, and treat S1 through S7 as increasing bridge IDs. Then S1 is the root. Most switches connect to it directly. S3 is two hops away, through either S2 or S5, and the lower ID, S2, wins the tie. That leaves six active links for seven switches, exactly a tree.

[00:13:19] (lec06-lan.pdf p41) Watch out for this one. When a switch floods an unknown destination, the frame doesn't become a broadcast. Its destination address stays exactly as it was. Only the set of output ports changed.

[00:13:35] (lec06-lan.pdf p41) Use this tree. Host A hangs off S3, host B off S7, and host C off S4. A to B cannot use the short-looking route through S5, because those dashed links do not forward.

[00:13:50] (lec06-lan.pdf p41) Trace the other two paths on the tree. What route does A to C follow? And B to C?

[00:14:06] (lec06-lan.pdf p41) A to C goes S3, S2, S1, S4. B to C goes S7, S1, S4. Notice that A to B took three hops, though the physical drawing offers something shorter. Spanning tree does not promise shortest paths between hosts, and it does not minimize total cost either. It promises one thing: no loops. Different priorities could pick a different tree, so the assumptions stay attached to the answer.

### 6.4 VLANs and trunks

[00:14:35] (lec06-lan.pdf p42) A building has one set of switches, but two departments that should not share broadcasts. Finance sits on three different floors, mixed in with engineering. Do we have to rewire the building each time someone changes desks?

[00:14:50] (lec06-lan.pdf p43) A virtual LAN lets one physical switching system act as several separate LANs. Group by organization rather than by location. A broadcast from a finance machine is now flooded only to finance ports, and engineering never sees it. A flood is confined to its VLAN, even though every frame crosses the same box.

[00:15:13] (lec06-lan.pdf p45) How does a switch know which VLAN a frame belongs to? There are two ways. With port-based VLANs, membership belongs to the port. Ports 1 through 8 are VLAN 10, and ports 9 through 16 are VLAN 20. Whatever plugs into that port joins that VLAN. With MAC-based VLANs, membership follows the machine's address instead, so a laptop keeps its VLAN wherever it plugs in.

[00:15:42] (lec06-lan.pdf p30,45) An independent-learning example. Ports 1 and 2 are VLAN 10. Ports 3 and 4 are VLAN 20. Port 5 is a trunk for both. Port 6 is in VLAN 10 but discards data. A frame from A enters port 1 for unknown B. Learn A in VLAN 10 on port 1. Flood only ports 2 and 5.

[00:16:08] (lec06-lan.pdf p30,45) The same MAC, A, enters port 3 in VLAN 20. Learn a separate entry for A in VLAN 20 on port 3. B is unknown in this VLAN too, so flood only ports 4 and 5. The VLAN 10 entry is still there. This example uses independent learning, rather than claiming all hardware organizes its memory identically.

[00:16:32] (lec06-lan.pdf p30,45) B replies on port 2 in VLAN 10. Learn B in VLAN 10 on port 2, then look up A within VLAN 10. The frame goes only to port 1. Neither the other VLAN nor the discarding port receives it.

[00:16:48] (lec06-lan.pdf p30,45) Finally B replies on port 4 in VLAN 20. Learn B in VLAN 20 on port 4, then look up A within that VLAN. Send only to port 3. The VLAN context chooses which learned location is relevant. The trunk can carry both groups while keeping their identities separate.

[00:17:08] (lec06-lan.pdf p47) Finance spans two switches, joined by one cable. That cable carries both departments. When a frame arrives at the far switch, how can it tell which VLAN the frame belongs to? The sending switch inserts a tag. This is 802.1Q trunking. It adds four bytes after the source address, including a 12 bit VLAN ID. Because the frame changed, the CRC is recomputed. The receiving switch reads the tag, and removes it before delivering to an ordinary host.

[00:17:43] (lec06-lan.pdf p49) Before leaving the LAN, compare the three boxes we now have. A hub gives you no traffic isolation, and it needs no setup. A switch isolates traffic, and it's still plug and play, but flooding and spanning trees keep it from routing efficiently. An IP router isolates traffic and routes well, but it isn't plug and play, because someone must configure it. Each step up costs something, and buys something.

[00:18:12] (lec06-lan.pdf p48) Keep the jobs separate. A VLAN decides who shares a broadcast domain. A trunk carries that identity between switches. Neither one moves traffic between different VLANs. For that, you need a router, even if the router lives inside a multilayer switch.

[00:18:31] (lec06-lan.pdf p48) The slide's phrase can mislead you here. A trunk carries frames between switches, keeping their VLANs separate. It doesn't move traffic from one VLAN to another. That takes a router.

[00:18:45] (lec06-lan.pdf p46) Change one thing. A finance laptop's owner moves desks, and plugs into a port in VLAN 20, the engineering VLAN, on a port-based switch.

[00:18:57] (lec06-lan.pdf p46) Whose broadcasts does the laptop hear now? And can it keep its old IP address and still work?

[00:19:12] (lec06-lan.pdf p46) It now hears engineering's broadcasts, because the port decided its membership. And if each VLAN is its own IP subnet, its old address no longer fits, so it needs a new configuration. The laptop is physically fine, yet logically it moved. Remember too that VLANs separate traffic, but they are no complete security proof. Addresses can be changed, and configuration decides what is accepted. That word, subnet, needs a real meaning. And it is the point where local delivery runs out. To go further, we need addresses with structure.

## Chapter 7: Lecture 7: IP packets

### 7.1 What the network promises

[00:19:49] (lec07-network1.pdf p4) Our laptop's frame has reached the edge of its LAN. Beyond that lie thousands of networks, built by different owners, from different hardware. What should the network as a whole promise to deliver? A guaranteed rate? Guaranteed order? Or almost nothing at all? The surprising answer that built the Internet is: almost nothing.

[00:20:16] (lec07-network1.pdf p8) One design comes from the telephone network: circuit switching. Before any data moves, set up a path, and reserve capacity at each hop. Once it is established, the bandwidth is yours. Quality is predictable. But if you pause, nobody else may use your reserved share, and every switch has to remember your call.

[00:20:41] (lec07-network1.pdf p8) Put numbers on the waste. A 1 megabit per second circuit reserved for ten seconds allocates up to 10 megabits. If the application sends only 2, the rest of that opportunity can't necessarily be used by anyone else.

[00:20:59] (lec07-network1.pdf p4) The other design is packet switching. Chop data into packets. Give each one its own destination address, and let each hop forward it when capacity becomes available. No setup, and no reservation. No router has to remember that you exist.

[00:21:20] (lec07-network1.pdf p5) Why does this suit computers? Their traffic is bursty. A web page arrives in a rush, and then the link goes silent. Sharing capacity according to actual arrivals is called statistical multiplexing, and it lets many bursty users share a link that could never hold all their peaks. The price comes when bursts overlap. If 8 megabits per second arrive at a 4 megabit link for 10 milliseconds, a backlog of 5,000 bytes builds in a queue.

[00:21:53] (lec07-network1.pdf p6) IP makes a modest deal called best-effort service. It will try. It may lose your packet, reorder it, delay it, or even duplicate it, and none of that breaks the contract. That sounds terrible, until you see what it buys. A network that promises so little can run over nearly any link, and needs no per-flow memory inside. Reliability can then be added at the end machines, by the programs that actually need it.

[00:22:25] (lec07-network1.pdf p14) Best effort is not the only possible deal. A QoS service model is a list of promises about bandwidth, loss, order, and timing. ATM's constant bit rate service reserves a fixed rate, with order and timing protected. ATM's available bit rate promises only a minimum rate. Integrated Services aims at explicit guarantees per flow. Differentiated Services treats classes of packets differently, without per-flow guarantees. Keep these promises separate. A minimum rate is not a delay bound, and priority is not an end to end guarantee.

[00:23:08] (lec07-network1.pdf p9) If routers remember nothing about flows, what do they keep? A forwarding table. And that exposes the most useful split in this course. The data plane handles every packet, using the installed table, in nanoseconds. The control plane exchanges information, and decides what belongs in that table, over seconds. The management plane is where people configure intent. Say an operator changes a link weight. A protocol recomputes. The router installs a new entry. Later packets follow it. Those are separate events, and that separation will matter when failures strike.

[00:23:55] (lec07-network1.pdf p13) Traditionally, each router runs its own control software, and they cooperate. Software-defined networking moves that logic into a controller, which programs the forwarding devices. Does every packet then have to visit the controller? No. The controller installs rules, and the device applies them locally. Either way, the rule stays the same. Control decides. Data executes.

[00:24:27] (lec07-network1.pdf p13) An easy mistake: if average load is below capacity, nothing should ever wait. But traffic comes in bursts, so queues still build for short moments.

[00:24:40] (lec07-network1.pdf p15) Test yourself on the contract. A packet has a valid address. Its checksum is perfect, and a route exists. It still never arrives.

[00:24:53] (lec07-network1.pdf p15) Did the network break its promise? Name two ways this could happen.

[00:25:06] (lec07-network1.pdf p15) No promise was broken. A full queue may drop it. Its TTL may expire. A failure or a policy may stop it. Best effort means exactly that. So what does the network truly require from each packet? An address that can guide it across thousands of networks, without each router knowing every host. That is our next problem.

### 7.2 Addresses and prefixes

[00:25:34] (lec07-network1.pdf p17) A switch can keep one table entry per machine, because a LAN is small. The Internet holds billions of interfaces. If every router needed an entry for every one, no router could cope. So how can a router in another country forward a packet toward your laptop without ever having heard of it?

[00:25:56] (lec07-network1.pdf p17) An IPv4 address is simply a 32 bit number, written as four decimal bytes. Here is our example, 10.10.1.97. It identifies an interface, not a computer, so a router with three links has three addresses. And unlike a MAC address, this one has structure.

[00:26:20] (lec07-network1.pdf p21) The structure is this. The leading bits name a network, and the trailing bits name a host within that network. The boundary is written after a slash. In 10.10.1.97/23, the first 23 bits are the network part, leaving 9 bits for hosts. A router far away only needs to know which way to send that whole block. Every host inside is covered by one entry. That is how the Internet scales.

[00:26:53] (lec07-network1.pdf p27) Originally that boundary was forced. Classful addressing offered only three unicast sizes: slash 8, slash 16, and slash 24. An organization needing 300 addresses was too big for a slash 24, so it received a slash 16, with 65 thousand addresses, and wasted nearly all of them.

[00:27:18] (lec07-network1.pdf p27) The class was even written into the address's first bits. An initial zero meant class A, one zero meant class B, and one one zero meant class C. Class D, beginning one one one zero, is multicast. Today the prefix is stated explicitly, so a first byte no longer implies a mask.

[00:27:42] (lec07-network1.pdf p29) CIDR, classless inter-domain routing, lets the boundary fall anywhere. Now the 300 address organization takes a slash 23, with 512 addresses. Each bit you add to the prefix halves the block. A slash 24 has 2 to the 8th, which is 256. A slash 23 has twice that. CIDR also allows aggregation. Two halves of one slash 24 can be announced as that single slash 24. But two ranges that merely look close may not combine, because a block must be aligned on its own size.

[00:28:24] (lec07-network1.pdf p30) Who hands out these blocks? Allocation is hierarchical too. ICANN allocates to regional registries. Those allocate to Internet providers and large institutions, who pass smaller blocks on to their customers. So 12.0.0.0/8 might contain 12.3.0.0/16, which contains 12.3.1.0/24. A provider can then announce one short prefix for all of its customers together. The address hierarchy mirrors the business hierarchy, and it's what keeps routing tables manageable. Compare that to a switch, whose table lists individual machines.

[00:29:12] (lec07-network1.pdf p23) To compute with a prefix, write it as a subnet mask. That is 32 bits with ones over the network part, and zeros over the host part. A slash 23 is 255.255.254.0. Now apply it. A bitwise AND of address and mask keeps the network bits, and clears the host bits. The result is the network address, 10.10.0.0. Notice what happened in the third byte. The 1 was cleared, because that last bit belongs to the host part.

[00:29:53] (lec07-network1.pdf p23) Do the opposite. Set every host bit to one, and you get the broadcast address of this subnet, 10.10.1.255. The all zeros and all ones host patterns are reserved. So this block has 512 addresses in total, and 510 usable ones, from 10.10.0.1 through 10.10.1.254.

[00:30:21] (lec07-network1.pdf p23) That subtraction of two applies to ordinary subnets. A slash 31 point to point link and a slash 32 host route need their own interpretation, so do not apply it blindly. The real rule is this. An address alone tells you nothing about its subnet. You need the mask.

[00:30:43] (lec07-network1.pdf p23) A tempting shortcut is to compare the first three bytes of two addresses. That only works for a slash 24. For any other prefix, apply the actual mask.

[00:30:57] (lec07-network1.pdf p24) A trap on purpose. In this same slash 23, consider the address 10.10.0.255. It ends in 255.

[00:31:11] (lec07-network1.pdf p24) Is it a broadcast address? Look at the host bits, not at the decimal number.

[00:31:31] (lec07-network1.pdf p24) No. Its host part is 0 11111111, and that first zero means the bits are not all ones. It is an ordinary host address, sitting in the middle of the block. The ending 255 only signals broadcast when the mask says the last byte alone is the host part. So the numbers are only half of the picture, and the other half is the header that carries them. Let us open that up.

### 7.3 The IPv4 header

[00:32:02] (lec07-network1.pdf p33) What does a router actually need to read? The IPv4 header has only about a dozen fields, and each exists to solve one bounded problem. Read them by purpose and by unit, because the units are where the traps are.

[00:32:20] (lec07-network1.pdf p33) The header. Version says 4. IHL, the header length, counts 32 bit words, not bytes. So a value of 5 means 20 bytes. A packet with IHL 6 and total length 1024 therefore has 24 header bytes, and 1000 bytes of payload.

[00:32:43] (lec07-network1.pdf p35) Total length counts the whole datagram in bytes, and it is a 16 bit field. So the largest value is 2 to the 16th, minus one, which is 65,535 bytes. The slide prints 63,535. That is a typo, and the arithmetic settles it. **Clarification:** The slide prints 63,535; the 16-bit Total Length maximum is 65,535 bytes (lec07 p35; RFC 791).

[00:33:07] (lec07-network1.pdf p39) The protocol field names what comes next, such as TCP, 6, or UDP, 17. It is not a port number. Follow the chain of hand-offs. Ethernet's type says this payload is IPv4. IPv4's protocol says this payload is UDP. UDP's destination port selects the program.

[00:33:35] (lec07-network1.pdf p38) TTL limits the damage from routing loops. Every router lowers it by one, and at zero the packet dies, and the router normally sends back an ICMP time exceeded message. A clever tool turns this into a map. Traceroute sends a probe with TTL 1. The first router replies. Then TTL 2, and the second router replies. Each reply reveals one more hop. A missing reply may just mean a router declines to answer.

[00:34:10] (lec07-network1.pdf p41) One more field is linked to TTL. The header checksum is a one's complement sum over the header only. It does not cover the payload, it does not authenticate anybody, and it cannot repair errors. And here is the consequence. Each router lowers the TTL, which changes the header. So each router must also update the checksum. With TTL 64, our example header's checksum works out to one value. With TTL 63, it is a different one.

[00:34:47] (lec07-network1.pdf p42) Read each field with its unit. IHL is in 32 bit words. Total length is in bytes. Fragment offset is in 8 byte units. TTL is in router hops. Mixing these up is how most header questions are lost.

[00:35:06] (lec07-network1.pdf p42) A common overclaim. The IPv4 checksum doesn't protect the payload, doesn't correct anything, and doesn't authenticate a sender. It only detects errors in the header.

[00:35:21] (lec07-network1.pdf p38) A new situation. A forwarding loop forms between R1 and R2, and a packet enters it with TTL 64. Meanwhile a DNS answer has a TTL of 300, and our switch table has a timer too.

[00:35:39] (lec07-network1.pdf p38) Does TTL rescue this packet? And do those three things called TTL all count the same thing?

[00:35:54] (lec07-network1.pdf p38) TTL does not rescue it. It only ends it, after using up link capacity, so the damage is bounded rather than prevented. And the three are different. IP's TTL counts router hops. A DNS TTL counts seconds of cache life. A switch table timer ages an entry locally. Same acronym, different arithmetic. One field group remains, those fragmentation fields, so let us use them.

### 7.4 Fragmentation

[00:36:28] (lec07-network1.pdf p35) IP runs over any link, and links limit how big a packet they will carry. That limit is the MTU. What happens when a 4,000 byte datagram reaches a link with an MTU of only 1,500 bytes?

[00:36:45] (lec07-network1.pdf p36) If fragmentation is allowed, the router splits it into smaller datagrams. Each fragment gets its own full IP header, so each travels independently. They all keep the original's identification number, so the destination can tell which ones belong together. Reassembly normally happens only at the destination.

[00:37:10] (lec07-network1.pdf p37) The arithmetic, carefully. Total length is 4,000, and 20 bytes of that is header. So the data to carry is 3,980 bytes. Each fragment on the small link can hold 1,500 minus 20, which is 1,480 bytes of data. And nonfinal fragments must carry a multiple of 8 bytes, because the offset field counts in 8 byte units. 1,480 divides evenly by 8. So 1,480 it is.

[00:37:47] (lec07-network1.pdf p37) The first fragment carries bytes 0 through 1,479, offset 0, more fragments flag set. The second carries the next 1,480. Its offset is 1,480 divided by 8, which is 185. The flag is still set. The third carries what remains, 1,020 bytes. Its offset is 2,960 divided by 8, which is 370, and its more fragments flag is 0, marking the end.

[00:38:25] (lec07-network1.pdf p37) Check it. The payloads sum to 3,980, which is the original data, restored exactly. But the total bytes sent are 4,040, not 4,000, because there are now three headers instead of one. Fragmentation costs overhead, and if any one fragment is lost, the whole datagram is lost.

[00:38:49] (lec07-network1.pdf p37) Keep the rule short. Offset is the data position in the original, divided by 8. It is not the fragment's length, and it does not count headers. Fragmentation exists to fit a link, and it has nothing to do with repairing congestion loss.

[00:39:09] (lec07-network1.pdf p37) One more trap. A router can't always fragment. If the Don't Fragment flag is set, it isn't allowed to. And losing any one fragment loses the whole datagram.

[00:39:24] (lec07-network1.pdf p37) New numbers. Total length 3,200, header 20, MTU 1,000. This time 1,000 minus 20 is 980, and 980 is not a multiple of 8.

[00:39:40] (lec07-network1.pdf p37) What is the largest nonfinal payload? How many fragments will there be, and what are their offsets?

[00:40:01] (lec07-network1.pdf p37) Round 980 down to a multiple of 8, and you get 976. The data is 3,180 bytes, giving payloads of 976, 976, 976, and a final 252. The offsets go up in steps of 122: 0, 122, 244, 366. Those four unused bytes per fragment are the price of 8 byte alignment. We now know what a packet looks like. Next question: how does an organization carve up its address space, and how does a router pick among overlapping routes?

## Chapter 8: Lecture 8: Subnets and forwarding

### 8.1 Carving a subnet

[00:40:48] (lec08-network2.pdf p3) Our laptop's network got its addresses from somewhere. An organization holds one block, and four departments of very different sizes. How do you cut the block so that everyone fits, nothing overlaps, and routers can still describe each piece with a single prefix?

[00:41:08] (lec08-network2.pdf p5) Start with size, not with addresses. A subnet with h host bits holds 2 to the h addresses. Two are reserved, for the network and the broadcast. So to hold H hosts, choose the smallest h where 2 to the h, minus 2, is at least H. The prefix length is then 32 minus h. Using different sizes inside one block is called variable length subnet masking.

[00:41:39] (lec08-network2.pdf p4) To feel the trade, take one slash 24 and start borrowing host bits for subnets. Borrow 1 bit: 2 subnets, with 7 host bits left, so 126 hosts in each. Borrow 2 bits: 4 subnets of 62 hosts. Borrow 3: 8 subnets of 30. Each borrowed bit doubles the number of subnets, and roughly halves their size. Keep going, and at 7 borrowed bits, only one host bit remains. The formula then gives zero ordinary hosts. A slash 31 needs its own point to point interpretation, so don't apply the subtraction blindly there.

[00:42:25] (lec08-network2.pdf p5) Why does a host care about all this? Because the mask is how it makes its first decision. Before sending, it ANDs the destination with its own mask, and compares that with its own network. If they match, the destination is on this link, so it sends directly. If not, it sends to its gateway. Routers apply masks too, but to a whole table of prefixes, as we'll see in a moment.

[00:42:56] (lec08-network2.pdf p7) The instructor's example. Four departments need 130, 120, 60, and 31 hosts, inside a slash 23. The slide labels the parent 128.101.5.0/23. Apply the mask, though. A slash 23 forces the last bit of the third byte to zero, and 5 is odd. So the true network is 128.101.4.0/23. It covers third byte values 4 and 5, and the slide's department blocks fit this normalized parent. **Clarification:** The slide's 128.101.5.0/23 normalizes to 128.101.4.0/23; the 31-host department needs /26 (lec08 p7).

[00:43:39] (lec08-network2.pdf p7) Allocate the largest first, since that keeps the blocks aligned. Department A needs 130. 7 host bits give only 126, so it takes 8 bits, a slash 24, the first half of the parent. B needs 120, and 7 bits give 126. That is a slash 25, at 128.101.5.0. C needs 60. 6 bits give 62, so a slash 26. D needs 31. It is tempting to pick a slash 27, because 32 addresses seem like enough. But a slash 27 leaves only 30 usable. So D also needs a slash 26.

[00:44:31] (lec08-network2.pdf p7) See the blocks laid along the parent. 256 plus 128 plus 64 plus 64 is 512, and that fills the slash 23 exactly. Each block begins on a multiple of its own size, which is what lets a single prefix describe it.

[00:44:52] (lec08-network2.pdf p7) Check any allocation three separate ways. Does each subnet have enough usable hosts? Do any overlap? And is each one contained in the parent? A plausible looking dotted address proves none of those.

[00:45:09] (lec08-network2.pdf p7) The mistake that looks harmless: placing a block wherever there's room. A block must begin on a multiple of its own size. Otherwise, no single prefix can describe it.

[00:45:24] (lec08-network2.pdf p5) Change one requirement. Department C's count of 60 did not include its router interface or its printers. The real requirement is 63 interfaces.

[00:45:38] (lec08-network2.pdf p5) What prefix does C need now? And does the whole plan still fit in the slash 23?

[00:45:58] (lec08-network2.pdf p5) 6 bits give only 62 usable, so C jumps to 7 bits, a slash 25, with 128 addresses. Add that up: 256, plus 128, plus 128, plus 64, is 576. That is more than 512, so the plan no longer fits. A single extra host at a boundary doubled the block, which is why you must state exactly what the count includes. The result is a table of overlapping prefixes on every router, so how does a router choose among them?

### 8.2 The longest match

[00:46:40] (lec08-network2.pdf p13) R1 holds a table of prefixes. Because prefixes can nest, one destination can match several entries at once. Which one should win? And how can a router decide this in a few nanoseconds, a few million times every second?

[00:46:59] (lec08-network2.pdf p29) A router's table with three entries. 201.10.0.0/21 goes out output A. Inside that block, 201.10.6.0/23 goes out output B. And 0.0.0.0/0 goes out output C. Those entries overlap on purpose. The slash 21 is an aggregate, the slash 23 is an exception carved out of it, and the slash 0 is the fallback.

[00:47:33] (lec08-network2.pdf p29) A packet arrives for 201.10.6.17. To test a route, mask the destination with the route's prefix length and compare. Under the slash 21 mask it matches. Under the slash 23 it also matches. And slash 0 matches everything. Three matches. The rule is longest prefix match. Choose the match with the most network bits, because it is the most specific claim. So the slash 23 wins, and the packet leaves on output B.

[00:48:12] (lec08-network2.pdf p29) 201.10.4.8. Its third byte, 4, lies within the slash 21, which covers 0 through 7, but not within the slash 23, which covers only 6 and 7. So output A. And 203.0.113.8 matches only the fallback, so output C. A route's position in the list does not matter. Neither does any metric from an unrelated route. Only prefix length decides among installed matches.

[00:48:49] (lec08-network2.pdf p15) Let's see this at the level of bits, because that's what the hardware does. Write the destination, 201.10.6.17, above the route's network, 201.10.6.0. Under a slash 23, only the first 23 bits count. Compare them. Every one matches, so this route matches. Whatever's to the right of the boundary doesn't matter. Now compare 201.10.4.8 against that same route. Look at the third byte. 4 is 00000100, and 6 is 00000110. They differ in bit 23, inside the prefix. So that's no match, and that second packet falls through to the shorter route.

[00:49:45] (lec08-network2.pdf p30) The speed problem. Scanning every route is far too slow. On a 10 gigabit link with 64 byte packets, there are about 19 and a half million packets each second, which leaves 51 point 2 nanoseconds per packet. That calculation leaves out Ethernet's physical overhead, so treat it as a budget illustration. But the conclusion holds. There is no time for a linear scan. **Clarification:** The 51.2 ns figure omits physical Ethernet overhead; it is a processing-budget illustration.

[00:50:16] (lec08-network2.pdf p31) One answer is a trie, a tree you walk one address bit at a time. Follow the destination's bits down from the root. Whenever you pass a node holding a route, remember it. If the path dead-ends deeper down, you still have the last route you remembered. That is why a failed deep branch does not lose the earlier match. A Patricia trie compresses long chains with no branching, and multi-bit nodes trade memory for fewer steps.

[00:50:47] (lec08-network2.pdf p32) The other answer is hardware. Ordinary memory takes an address and returns the content. Content-addressable memory does the reverse. Give it a key, and it compares against every entry at the same time. A plain CAM needs exact matches, which suits MAC tables. Prefixes have don't care bits. TCAM adds a third state, so a stored entry can say these bits must match, and these do not matter. Several entries can still match, so hardware priority must favor the longest prefix.

[00:51:26] (lec08-network2.pdf p11) Once you can match bit patterns, why stop at the destination? Generalized forwarding matches on selected header fields and applies a configured action, such as forward, drop, or rewrite. That connects back to software-defined networking. Whether by prefix or by general match, the principle holds. Control installs the rules. The data plane applies them, one packet at a time.

[00:51:57] (lec08-network2.pdf p11) The classic slip is stopping at the first match, or taking the lowest cost. In a table, order doesn't matter. In a trie, you keep walking, and remember the longest valid prefix so far.

[00:52:13] (lec08-network2.pdf p29) Add a route. An operator installs 201.10.6.16/28 going to a new output, D, and a metric says the slash 21 is an excellent path. Our first packet, 201.10.6.17, comes back through.

[00:52:34] (lec08-network2.pdf p29) Which output does it take now? And what would 201.10.6.33 do?

[00:52:55] (lec08-network2.pdf p29) The slash 28 covers 201.10.6.16 through 31, so 201.10.6.17 goes to D. The metric never entered into it. And 201.10.6.33 is outside the slash 28, so the slash 23 catches it, output B. Finding the output is only half of forwarding, though. The packet still has to physically cross the router. So let us go inside.

### 8.3 Inside a router

[00:53:29] (lec08-network2.pdf p9) A router has found the right output. Now a packet must physically cross the machine, while packets arrive on every other port too. Where can this go wrong? When a router is slow, which part is actually the bottleneck?

[00:53:47] (lec08-network2.pdf p9) A router has four main parts. Input ports receive the bits, check the link layer, and do the lookup. A switching fabric moves packets between ports. Output ports buffer and transmit them. And a routing processor runs the control plane, computing the tables that input ports use. Follow our packet: in, lookup, across, queue, out.

[00:54:16] (lec08-network2.pdf p19) The fabric's capacity is the first limit. With 4 inputs, each at 10 gigabits per second, up to 40 gigabits per second may be offered. A fabric that cannot move that much makes inputs wait, even when every output is free. There are three classic designs.

[00:54:37] (lec08-network2.pdf p20) The oldest design is memory switching. The packet is copied into shared memory, and then copied out again. Each packet crosses memory twice, so memory bandwidth must be double the useful throughput.

[00:54:53] (lec08-network2.pdf p20) Put a number on it. If a memory system can sustain 20 gigabits per second of copying, each forwarded bit is copied twice, so the router tops out near 10 gigabits per second, before any other overhead.

[00:55:10] (lec08-network2.pdf p21) Next is a shared bus. A packet crosses directly from input to output, over one internal bus. That avoids the double copy. But only one packet can use the bus at a time, so the bus speed caps the entire router.

[00:55:28] (lec08-network2.pdf p21) Again, a number. Four 10 gigabit inputs feed a 20 gigabit bus. They offer 40 gigabits per second, and only 20 can cross, even if every output link sits idle. The bus is the bottleneck, before the outputs are even considered.

[00:55:50] (lec08-network2.pdf p22) The third design is an interconnection network, such as a crossbar. Now input 1 to output 2 and input 2 to output 1 can transfer at the same moment, over separate crossing points. Clos networks build big fabrics out of small switching stages. Many of them chop packets into fixed internal cells. Those cells are an internal technique, not IP fragments.

[00:56:18] (lec08-network2.pdf p22) There's still a limit. Input 1 to output 2 and input 2 to output 1 can move together. But send both inputs to output 1, and they contend for that one output. Parallel paths inside the fabric create no extra capacity at a single output.

[00:56:38] (lec08-network2.pdf p24) Even a crossbar has a trap. If two inputs want the same output at once, one must wait. Say input B and input C both have a head packet for output 1. B wins. C's head packet stays blocked. Now look behind it. C's second packet wants output 2, and output 2 is idle. But the queue is first in, first out, so that packet is stuck behind the blocked head. This is head of line blocking. A free output sits unused because of how the queue is arranged.

[00:57:16] (lec08-network2.pdf p25) Packets can also wait at the output, and this limit is physical. Three 1,500 byte packets arrive together at a 12 megabit per second output. Each needs 1 millisecond to transmit. So they finish at 1, 2, and 3 milliseconds, after waiting 0, 1, and 2. A faster fabric can't help, because the wire has a fixed rate. If arrivals keep exceeding that rate, the buffer eventually fills, and something is dropped. A drop policy chooses what to discard. A scheduler chooses what to send next. Priority shifts who suffers, but it creates no new bits per second.

[00:58:03] (lec08-network2.pdf p34) Step back from the queues, and look at the timescales in this machine. The data plane forwards, buffers, and schedules, in nanoseconds per packet, in line card hardware. The control plane runs routing and signaling, in tens of milliseconds to seconds per event, in router software. The management plane is people and scripts doing analysis and configuration, in minutes to hours. Tables could be typed in statically, but static entries don't adapt to failures, new equipment, or load.

[00:58:40] (lec08-network2.pdf p35) It's also a good moment to compare our two forwarding worlds, as the instructor's questions do. Are both MAC and IP addresses allocated hierarchically? Yes, both are: MAC blocks go to vendors, and IP blocks go down through registries. Which is organized by topology? Only IP. Which forwards by exact match? MAC, since IP uses longest prefix. Which builds its table automatically, by watching data? Ethernet switches. Which keeps per-host state in the network? MAC. Routers keep state per prefix. And which keeps per-connection state? Neither one. These answers are worked out from the lecture's material, as the slide gives no key.

[00:59:35] (lec08-network2.pdf p26) Before proposing a fix, find the contention. Is it at lookup, in the memory or bus or fabric, in an input queue, or at the output? Upgrading one simply moves the bottleneck to another.

[00:59:51] (lec08-network2.pdf p26) Careful with memory switching. Its internal copy rate is not its useful throughput. Each packet crosses memory twice, so useful throughput is half.

[01:00:04] (lec08-network2.pdf p25) Picture this. Ten senders all saturate one 10 gigabit output. Somebody proposes doubling the fabric speed.

[01:00:15] (lec08-network2.pdf p25) Will it help? What would a bigger buffer do instead?

[01:00:28] (lec08-network2.pdf p25) It won't. Packets just reach the same full output sooner. A bigger buffer absorbs short bursts, but under persistent overload it only adds delay before the same drops. The output's rate is the limit. That finishes the forwarding path, given a table. We assumed our laptop already knew its own address, its router, and its destination. It knew none of them when it woke up. So how does it find out?

## Chapter 9: Lecture 9: Discovery

### 9.1 Getting an address and a neighbor

[01:01:00] (lec09-discovery.pdf p4) Rewind to the moment the laptop wakes up. It holds one thing: its burned-in MAC address. It has no IP address, no mask, no idea where the router is, and no way to translate a name like www.example.test. How does it get from knowing nothing to sending a packet?

[01:01:24] (lec09-discovery.pdf p5) It needs three kinds of identifier, because they answer three different questions. A name is for people, and it can stay the same when a service moves. An IP address says where an interface sits in the topology. A MAC address gets a frame across one local link. Each translation between them is a separate protocol. That indirection is what lets a server change its address while its name stays fixed.

[01:01:55] (lec09-discovery.pdf p6) The habit to build. Before naming a protocol, state the missing fact. I need my own address and my gateway: that is DHCP. I need the MAC address of my next hop: that is ARP. I need the IP address behind a name: that is DNS.

[01:02:16] (lec09-discovery.pdf p14) Start with the bootstrap problem. The laptop needs to ask a server for an address. But it has no address to send from, and it doesn't know where any server is. There is a way out of that circle. Local broadcast reaches everyone on the LAN, with no configuration at all. So DHCP begins with a shout.

[01:02:41] (lec09-discovery.pdf p17) Four messages follow. Discover: is any DHCP server out there? Offer: a server proposes an address, say 192.0.2.10, along with a mask, a gateway, a DNS resolver, and a lease time. Several servers might offer. Request: the client announces which offer it chooses. ACK: that server confirms. Only after the ACK does the client begin using the address. An offer alone is just a proposal.

[01:03:18] (lec09-discovery.pdf p17) Look at what the laptop now knows. Its address, 192.0.2.10, with a slash 24 mask. Its gateway, 192.0.2.1. Its resolver, 198.51.100.53. It knows what counts as local, and where to send everything else. Yet it still does not know the gateway's MAC address. Knowledge arrives in stages, not in one magic connected moment.

[01:03:55] (lec09-discovery.pdf p18) Why does the address come with a lease? Suppose a laptop crashes, or simply leaves. It never says goodbye. If allocations were permanent, the pool would slowly drain. With a lease, the allocation expires unless it is renewed. This is called soft state: information that disappears on its own unless refreshed. Failed machines clean up after themselves, by doing nothing. A reservation is different. An administrator configures a fixed address for a particular machine, and the server hands it out centrally each time.

[01:04:36] (lec09-discovery.pdf p24) The laptop wants to send through its gateway, 192.0.2.1. A frame needs a MAC address, and it has only an IP address. So it checks its ARP cache. Empty. It broadcasts: who has 192.0.2.1? Every machine on the LAN hears. Only R1 replies, directly: that's me, and here is my MAC. The laptop caches that mapping for a while. Another soft state table.

[01:05:14] (lec09-discovery.pdf p25) ARP resolves only the next local hop, never the whole path. And don't confuse it with the switch's table. The host's ARP table maps IP to MAC. The switch's table maps MAC to port. Both changed during that exchange, and neither replaces the other. The rule is: route first, resolve the next hop's MAC second, transmit third.

[01:05:41] (lec09-discovery.pdf p25) Keep these lookups apart. ARP doesn't resolve a hostname, and DNS doesn't choose the Ethernet destination. DNS maps a name to an IP. ARP maps an IP to a MAC.

[01:05:57] (lec09-discovery.pdf p25) Change the target. The laptop now wants to send to the DNS resolver, 198.51.100.53. Apply the slash 24 mask to both addresses. 192.0.2.0 is not 198.51.100.0.

[01:06:21] (lec09-discovery.pdf p25) Which IP address does the laptop put in its ARP request?

[01:06:33] (lec09-discovery.pdf p25) It asks for the gateway, 192.0.2.1, never for the resolver, because ARP cannot cross a router. If the resolver were on the same subnet, at 192.0.2.53, it would ARP for the resolver directly. So the mask chooses the next hop, and the next hop chooses the ARP target. The laptop can now reach its resolver. But what does a resolver actually do? How can any system answer for every name on Earth?

### 9.2 Finding a name

[01:07:10] (lec09-discovery.pdf p26) The browser has the name www.example.test. It needs an address. There are billions of names, changing constantly, owned by millions of organizations. Could one file hold them? Could one giant server answer them all?

[01:07:31] (lec09-discovery.pdf p27) The two obvious designs fail. A hosts file downloaded by everyone would be enormous, and always stale. One central server would be a single point of failure, a traffic bottleneck, and far away from most people. So DNS distributes the database, by splitting up responsibility.

[01:07:54] (lec09-discovery.pdf p30) Names form a tree, read from the right. The root delegates to top-level domain servers, such as dot test or dot com. Those delegate to authoritative servers for each organization's zone. A zone is a piece of the tree under one administration. Nobody holds everything. Each server only knows who to ask next. By the way, you may hear about 13 root servers. That is 13 named identities, A through M, each deployed as many physical instances around the world. **Clarification:** 13 refers to root identities A to M, each deployed as many instances (lec09 p31).

[01:08:31] (lec09-discovery.pdf p36) Follow one lookup with empty caches. The laptop asks its resolver: please find this name for me. That is a recursive query. It asks the server to do all the work. The resolver then asks the root. The root doesn't know the answer, but it gives a referral: ask the dot test servers. The resolver asks those, and gets another referral: ask example dot test. It asks that authoritative server, and gets the answer. Those are iterative queries. Each returns an answer or a pointer, and leaves the next step to the asker. The result returns to the laptop: 203.0.113.80.

[01:09:20] (lec09-discovery.pdf p36) One lookup uses both styles. The client to resolver request is recursive. The resolver's walk down the tree is iterative. An exam question that asks which one DNS uses is really asking, which hop?

[01:09:37] (lec09-discovery.pdf p37) Doing all that for every request would crush the root. So the resolver caches. Each answer carries a TTL, in seconds. Store a record with TTL 300 at noon, and it can be reused until 12:05. Now the catch. If the real address changes at 12:01, the cache keeps giving out the old one for four more minutes. A shorter TTL narrows that window, at the cost of more lookups. That's a straight trade between freshness and load. Resolvers also cache referrals, so most queries never touch the root.

[01:10:19] (lec09-discovery.pdf p38) Resolvers remember failures too. Negative caching stores the answer that a name doesn't exist. Repeated typos, like www dot example dot tesst, then fail quickly, instead of walking the tree each time. There's a downside. A brand new name might stay hidden behind an unexpired negative answer. And don't confuse a genuine no such name result with a mere timeout.

[01:10:49] (lec09-discovery.pdf p38) Imagine someone keeps typing a name with a letter missing. Once the resolver learns that name doesn't exist, it can fail those requests quickly, until the negative result expires. A timeout is different. It only means no answer arrived, not that the name is missing.

[01:11:10] (lec09-discovery.pdf p38) Same word, different meaning. A DNS TTL is a cache lifetime, in seconds. An IP TTL is a hop limit. And a switch's aging timer is different again.

[01:11:26] (lec09-discovery.pdf p38) Change the state of the cache. A second laptop on the same LAN asks for www.example.test 4 minutes after the first one. The resolver stored the record with TTL 300.

[01:11:43] (lec09-discovery.pdf p38) How many queries does the resolver send to the hierarchy? And what about a third laptop at 5 minutes exactly?

[01:12:05] (lec09-discovery.pdf p38) At 240 seconds the cache is still valid, so zero queries leave the resolver. At 300 seconds the entry has expired, so it must ask again, though a cached referral could skip the root. Caching removes hierarchy traffic only. The packets to the web server still need routes and frames. Next, let us see what else this database holds.

### 9.3 Records and the whole journey

[01:12:33] (lec09-discovery.pdf p41) A DNS answer isn't just a name and an address. How does the same system tell you where to send email, or which server is in charge of a zone? And what happens if the question or its answer simply gets lost?

[01:12:50] (lec09-discovery.pdf p41) DNS stores typed resource records, each with a name, a type, a value, and a TTL. An A record maps a name to an IPv4 address. An NS record names the server authoritative for a zone. A CNAME maps an alias to its canonical name. An MX record names a domain's mail exchanger, with a preference. Notice that NS, CNAME, and MX values are hostnames, not addresses. So they may need another lookup, to find an address.

[01:13:28] (lec09-discovery.pdf p43) DNS usually runs over UDP, which recovers nothing. So reliability is built above it. Zones keep replicated servers. Clients use timeouts, retry, and try a different server. Replies are matched to questions by an ID. DNS can also use TCP, so UDP is common, not exclusive.

[01:13:55] (lec09-discovery.pdf p43) Walk through a failure. A resolver queries server A, and hears nothing. After its timer, it tries replica B, and it accepts a reply only if it matches the outstanding request. Repeating immediately to the same failed server would add load, without helping.

[01:14:16] (lec09-discovery.pdf p49) We can tell the whole story in order, and there's a surprise in it. To reach the name, the laptop must query the resolver. But the resolver is remote. So before the DNS query can even leave, the laptop must ARP for its gateway. Then the frame goes to R1, carrying a packet to the resolver. The DNS answer returns. Only then can it send to the server, and a TCP connection can begin. The recap slide compresses that handshake. The classic form ends with a final ACK after the SYN and SYN-ACK. **Clarification:** The recap compresses the TCP handshake; SYN and SYN/ACK are followed by a final ACK (lec10 p8).

[01:14:56] (lec09-discovery.pdf p44) How does a new name enter this system? Say a startup called FooBar registers foobar.com. The registrar inserts two records into the dot com servers: an NS record saying that foobar.com is served by dns1.foobar.com, and an A record giving that server's address. That second one is needed, because otherwise you'd have to resolve dns1.foobar.com in order to reach the server that answers for foobar.com. On its own server, FooBar then adds an A record for www, and an MX record for mail.

[01:15:35] (lec09-discovery.pdf p45) You can watch all of this with a tool called dig. A plain query prints three sections. The answer section has the record you asked for. The authority section names the servers responsible for that zone. The additional section gives those servers' addresses, which saves another lookup. An address shown under additional isn't necessarily the web server you asked about. Running dig with plus trace shows the entire walk from root to TLD to authoritative. And asking a TLD server directly, with recursion off, returns no answer at all, only a referral. That's an iterative reply, visible in plain text.

[01:16:21] (lec09-discovery.pdf p55) The instructor's slides run this as a compact example: host A, router R, host B. A's address is 111.111.111.111, and B's is 222.222.222.222. A's mask says that B is off-subnet, so A uses ARP to learn R's near-side MAC. The frame runs from A's MAC to R's MAC, while the IP header reads A to B.

[01:16:54] (lec09-discovery.pdf p55) R removes the frame, looks up B's prefix, finds B's MAC on the outgoing subnet, and emits a new frame from its far-side MAC to B's MAC. There it is again: the Ethernet destination is R on one link, and B on the other. The IP endpoints never change, in this ordinary trace with no NAT.

[01:17:17] (lec09-discovery.pdf p58) There's no fixed order that says DNS comes before ARP. What is missing right now decides what happens next. The name's address is missing, so we need DNS. To reach DNS, we need the gateway's MAC, so we need ARP first. Discovery traffic has its own delivery dependencies.

[01:17:41] (lec09-discovery.pdf p58) A frequent confusion. A CNAME is not an HTTP redirect. It's an alias inside DNS, so the resolver just looks up another name. The browser never gets sent to a new URL.

[01:17:58] (lec09-discovery.pdf p58) Change three facts. Put the resolver on the laptop's own subnet. Make the DNS answer already cached. And then cut the link between R1 and R2.

[01:18:12] (lec09-discovery.pdf p58) For each change, which steps disappear, and which still have to happen?

[01:18:25] (lec09-discovery.pdf p58) A local resolver means the laptop ARPs for the resolver directly. A cached answer removes the hierarchy queries, but the web packet still needs its gateway and its routes. And a cut link? All of the laptop's DNS and ARP entries remain perfectly correct, yet delivery still fails, because R1's forwarding table is now wrong or incomplete. That table is the one piece we've taken for granted since the start. Who fills it in? That is routing.

## Chapter 10: Lecture 10: Routing

### 10.1 Dijkstra

[01:19:00] (lec10-routing.pdf p19) We ended the last chapter with a cut link, and a router whose table had gone wrong. So who fills in that table? A router forwards a packet using a table it reads in nanoseconds. But something has to build that table, and rebuild it when the network changes. An administrator cannot type routes into thousands of routers by hand. So how can routers, talking only to each other, work out good paths through a network none of them can see all at once?

[01:19:33] (lec10-routing.pdf p19) Remember our laptop's packet, sitting at router R1, headed for a web server. R1 looked up the destination, and sent it out one port. This chapter is about where that table entry came from.

[01:19:49] (lec10-routing.pdf p12) Start by separating two words. Forwarding is what a router does to one packet, right now: read the address, look it up, and send it out. Routing is how the table got there in the first place, a network-wide process of exchanging information and computing paths. And a route to a far prefix needs two pieces of knowledge. Which router, or exit, can reach that prefix? And how do I reach that router from here? This lecture solves the second piece. BGP will supply the first. Could you just type all this in by hand? Static routes don't adapt to failures, new equipment, or load.

[01:20:35] (lec10-routing.pdf p19) First we need a model. Draw the network as a graph, with routers as nodes and links as edges, each with a cost. A path's cost is the sum of its edge costs. Our goal is the cheapest path from a source to each destination. If every edge costs one, this just counts hops.

[01:20:58] (lec10-routing.pdf p19) But weights change the answer. Here, going from A to C directly costs 5. Going through B costs 2 plus 1, which is only 3. So the path with more hops is the better one. This makes sense inside one organization, where everyone agrees what the numbers mean. We'll see later that it does not fit the whole Internet.

[01:21:24] (lec10-routing.pdf p22) One approach is link-state routing, and its idea has two steps. Step one: every router tells everyone about its own links. Those messages flood through the whole network, so eventually every router holds the same map. Step two: each router independently runs a shortest path computation on its copy of that map, with itself as the source. It shares facts, not conclusions. OSPF and IS-IS are the two link-state protocols you will meet in practice, both used inside a single organization.

[01:22:02] (lec10-routing.pdf p22) One caution about that shared map. It's what the router currently believes, not a perfect live view of the network. If a link has just failed, some routers don't know yet. Hold on to that thought, because it creates a whole chapter of trouble. For now, assume every router's map is correct, and look at the computation itself, which comes from Edsger Dijkstra.

[01:22:31] (lec10-routing.pdf p22) Dijkstra's algorithm grows a region of settled nodes, whose best distances are final. It keeps a tentative distance for every other node. Then it repeats one step. Pick the unsettled node with the smallest tentative distance, and settle it. Next, relax its edges: for each neighbor v, ask whether going through this node beats the best distance we had. Why is it safe to settle that smallest node? Because weights are not negative, so any other route to it would have to leave through a node that is already at least as far. No detour could ever come back cheaper.

[01:23:13] (lec10-routing.pdf p27) Run it from A. Start by settling A, at distance zero. Its neighbors get tentative distances equal to their direct costs: B is 2, and C is 5. D is not adjacent, so D is infinity.

[01:23:30] (lec10-routing.pdf p28) The frontier holds B at 2, C at 5, and D at infinity. The smallest is B, so settle it, and record that its predecessor is A. Relax B's edges. Through B, C costs 2 plus 1, which is 3. That beats 5, so C improves, and its predecessor becomes B. Through B, D costs 2 plus 4, which is 6, and that beats infinity.

[01:24:00] (lec10-routing.pdf p30) The frontier is C at 3, and D at 6. Settle C, through B. Relax its edge to D: 3 plus 2 is 5. That beats 6, so D improves again, and its predecessor changes from B to C. See how a tentative value can keep getting better until the moment it's settled, and never after that.

[01:24:25] (lec10-routing.pdf p36) Finally settle D, at 5, through C. Every node is settled. The green edges form a shortest path tree, rooted at A. Final distances: B is 2, C is 3, and D is 5.

[01:24:41] (lec10-routing.pdf p36) The part that catches people out. The computation gave us predecessors, but a forwarding table needs something else. D's predecessor is C. That is the node just before D on the path. But router A cannot hand a packet to C. It is not even the right neighbor. The path to D is A, B, C, D, so A's forwarding entry says: to reach D, send to B. In fact, every entry at A says B here. Distance, predecessor, and first hop are three different outputs. The first hop is the only one a forwarding table stores.

[01:25:24] (lec10-routing.pdf p26) Try the instructor's exercise. On this graph, find the shortest path from t to v. It's tempting to go through x, since t reaches x directly at 5. But then x to z to y to v adds 3, for a total of 8. The direct route from x to v, at 4, also gives a total of 8 by way of s and w. The best path is t, s, w, x, z, y, v, adding 2, 1, 1, 1, 1, and 1, which is 7. So the distance is 7, answer B, and the forwarding entry at t points to s, also answer B. More hops, lower cost.

[01:26:11] (lec10-routing.pdf p36) The slides also trace a bigger graph from source A, over eight nodes. The method doesn't change. Settle B at 2, which improves D from 5 to 4, and gives E 9 and F 14. C and D then tie at 4. Either may go first, since a tie can alter a predecessor but no shortest distance.

[01:26:35] (lec10-routing.pdf p36) Settling D improves E to 8, and gives G 7. Settling G offers E another route costing 8, another tie. Settling E improves H from 14 to 13. And F stays at 14, since going through H would cost 16. Check any of these by adding the edges along the final path. Keep your settled set, tentative distances, and tie policy all explicit, and it's mechanical.

[01:27:07] (lec10-routing.pdf p36) Don't confuse the two sets. A tentative distance can keep improving. A settled one is final, and that's only guaranteed because weights aren't negative.

[01:27:19] (lec10-routing.pdf p36) Return to our small graph, and change one number. Raise the cost of the link between B and C from 1 to 6. Everything else stays the same.

[01:27:32] (lec10-routing.pdf p36) Run Dijkstra in your head. What are the three distances now? And which neighbor does A use to reach C?

[01:27:54] (lec10-routing.pdf p36) Settle B at 2. Through B, C would now cost 8, which doesn't beat the direct 5. D becomes 6 through B. Then settle C at 5. Through C, D would cost 7, which doesn't beat 6. So the distances are 2, 5, and 6. A's first hop to B is B, to C is C itself, and to D is B. One number changed, and A's route to C changed completely. But before A could install this, the new cost had to reach it. Flooding carries the whole map to everyone. What if routers shared something much smaller instead?

### 10.2 Distance vector

[01:28:38] (lec10-routing.pdf p37) Link state asks every router to store and process a map of the whole network. Could a router find good paths knowing almost nothing, just by asking its neighbors one simple question? How far are you from the destination?

[01:28:55] (lec10-routing.pdf p37) That's distance-vector routing. No router keeps a map. Each one keeps a list of destinations and its best known distance to each, and it tells that list only to its direct neighbors. Then each router combines what its neighbors said with the cost of reaching them. It's like asking for directions. You can't see the route. But if your neighbor says they're 3 kilometers from the station, and they are 3 kilometers from you, then you know something about your own distance.

[01:29:29] (lec10-routing.pdf p40) Compute one. A's link to B costs 3, and B says it's 3 away from Z. That's a total of 6. A's link to C costs 2, and C says 5. That's a total of 7. The minimum is 6, through B. So A's distance is 6, and its next hop is B. A doesn't know B's internal path to Z, and it doesn't need to. Now B advertises something new: its distance is 10. Through B would now cost 13. Through C still costs 7. So A switches to C, and its table changes with no map in sight.

[01:30:12] (lec10-routing.pdf p38) The rule, called the Bellman-Ford update. x is me. y is the destination. v ranges over my neighbors. My distance to y is the minimum, over all neighbors v, of my link cost to v, plus v's advertised distance to y. And the neighbor that gives the minimum becomes my next hop. Two terms, and they come from different places. The first I can measure myself. The second I'm trusting my neighbor about.

[01:30:45] (lec10-routing.pdf p42) How does a whole network find its answers? Knowledge spreads in rounds. Use our graph from before, and an idealized synchronous exercise: in each round, every router uses only the advertisements from the previous round. In round one, each router knows just itself and its direct neighbors. So A has B at 2, C at 5, and D at infinity.

[01:31:13] (lec10-routing.pdf p43) Round two. A hears B's vector from round one. B says it's 1 from C, and 4 from D. So through B, C costs 2 plus 1, which is 3. And D costs 2 plus 4, which is 6. A's table now reflects paths of up to two edges.

[01:31:35] (lec10-routing.pdf p44) Here's the subtle step. During round two, B also heard from C, and learned it can reach D for 1 plus 2, which is 3. In round three, B advertises that better number. A computes 2 plus 3, which is 5, through B. It has discovered the path A, B, C, D, without ever knowing that C was involved. The next round changes nothing, so it has converged, on the same answers Dijkstra gave.

[01:32:08] (lec10-routing.pdf p38) Those neat rounds are a classroom picture. Real routers update whenever they like, with no global clock. A value from a neighbor could also be old, not a final truth. RIP and EIGRP are the named members of this family. RIP uses hop count as its metric. Don't assume EIGRP behaves identically, because its rules differ in detail.

[01:32:35] (lec10-routing.pdf p38) Classify them. OSPF and IS-IS belong with link state. RIP and EIGRP belong with distance vector. RIP gives each link a hop cost of 1, so usable distances run from 1 to 15, and 16 means unreachable. Only RIP has that limit, as far as this lecture shows, so don't carry it over to EIGRP.

[01:33:02] (lec10-routing.pdf p46) Compare what's being trusted. Link state trusts link facts, and computes its own paths. Distance vector trusts its neighbors' computed results. Both reach shortest paths with a shared metric. But they share different knowledge, and that decides how they behave when things break. The reusable distinction is simple: a map, versus neighbors' distances.

[01:33:30] (lec10-routing.pdf p46) The lecture adds a broad comparison, and you should treat it as a family-level teaching picture, rather than a universal benchmark. Link state sends more messages, since facts flood everywhere, and each router runs its own computation. If one router computes something wrong, that error stays mostly local. Distance vector exchanges only with its neighbors. But a wrong number is passed along as if it were a fact, so one router's error can spread through everyone's tables. Real costs depend on graph size and on protocol details.

[01:34:08] (lec10-routing.pdf p46) In a synchronous trace, here's where marks get lost. Every router computes from the previous round's advertisements. Mixing in values from the current round changes the answer.

[01:34:23] (lec10-routing.pdf p41) You do one. Router x has two neighbors. Its link to P costs 4, and P advertises 7 to the destination. Its link to Q costs 9, and Q advertises 1.

[01:34:39] (lec10-routing.pdf p41) Which neighbor wins? Then suppose P's link cost rises to 6. Does your answer change?

[01:35:01] (lec10-routing.pdf p41) P gives 11, and Q gives 10, so Q wins, even though its link is the expensive one. Raise P's link to 6, and P only gets worse, at 13, so Q still wins. Notice that the router is relying on a number somebody else told it. It has no way to know how that number was produced, and no way to know whether the path behind it runs right back through itself. We'll come back to exactly that danger. First, there's one situation where neither of these approaches works at all.

### 10.3 Path vector

[01:35:38] (lec10-routing.pdf p47) Between organizations, neither method fits. Would your company publish its internal map to its competitors, as link state needs? Would it accept a single cost number from them, whose meaning it can't check? Networks run by different owners need something else.

[01:35:58] (lec10-routing.pdf p48) Consider why each one breaks down. Link state floods topology, which reveals private structure, and it requires a common metric. Distance vector hides the structure, so it's on the right track. But one bare number has two problems. Different networks measure cost differently, so the numbers aren't comparable. And the number hides the route, so nobody can apply a preference such as, avoid that competitor.

[01:36:29] (lec10-routing.pdf p50) The fix is to advertise the whole path. Instead of saying, I'm 3 away, a network says, I can reach it through networks 3, 2, 1. Each network that passes this along adds its own identifier at the front. This is path-vector routing, and it's the basis of BGP.

[01:36:52] (lec10-routing.pdf p51) Benefit one is easy loop detection. Say AS 3 offers the path 3, 2, 1 back to AS 1. AS 1 looks through the list, sees itself, and rejects it. It doesn't need to count, or wait. The loop is visible right there in the data.

[01:37:13] (lec10-routing.pdf p52) Benefit two is policy. Now that you can see the whole route, you can apply your own judgment. A network may prefer a longer path, for business reasons. It may avoid one that crosses a particular network. It may decide not to pass a route on to some neighbor. There's no shared definition of best anymore. That flexibility is the point. But it also means that loop-free does not imply everyone's choices fit together. We'll return to that.

[01:37:49] (lec10-routing.pdf p52) Don't overclaim here. Rejecting paths that contain your own AS stops loops. It doesn't promise immediate convergence, and it doesn't rule out policy oscillation.

[01:38:03] (lec10-routing.pdf p51) Test the rule. AS 4 receives the path 3, 2, 1. Next, AS 2 receives the path 3, 4, 2, 1. And then AS 5 is offered a path of length two and a path of length five.

[01:38:21] (lec10-routing.pdf p51) Which paths get rejected as loops? And must AS 5 choose the shorter one?

[01:38:35] (lec10-routing.pdf p52) AS 4 accepts: it isn't in the list. AS 2 rejects: its own number appears. And AS 5 may take either one. Its local policy can prefer the longer path. Path vector tells it what's possible, and it decides what's best. One routing idea remains in this lecture, and it asks a different question. Once a path is known, must every router really look up the address all over again?

### 10.4 MPLS labels

[01:39:07] (lec10-routing.pdf p53) Every router on a path repeats a longest prefix match, for the very same packet. And all traffic to one destination follows the shortest path, even when another route has spare capacity. Could we set up a path in advance, and just follow it?

[01:39:27] (lec10-routing.pdf p54) That's what MPLS does. At the edge of the network, an ingress router classifies the packet, and pushes a short label in front of the IP header. Routers inside read only the label, and look it up in a small exact table. The label says which prepared path this packet is on. The last router pops the label, and ordinary IP takes over.

[01:39:54] (lec10-routing.pdf p56) Labels only have local meaning. Label 17 reaches R2, whose table says: incoming 17, swap to 42, and send on this interface. Then R3 sees 42, and its table says to pop. Each router picks its own numbers, so the label changes at each hop while the path stays fixed. Does that remind you of something? The label behaves just like the yellow envelope. Only the IP header stays the same throughout.

[01:40:29] (lec10-routing.pdf p53) Who installed those table entries? Signaling. Before any data flows, messages travel along the chosen path, setting up state at each router. The lecture names RSVP, and for MPLS traffic engineering, the specific extension is RSVP-TE. Because the path is explicit, an operator can steer some traffic away from the shortest route, onto spare capacity. That is traffic engineering. **Clarification:** For MPLS tunnels the specific extension is RSVP-TE (lec10 p53; RFC 3209).

[01:41:01] (lec10-routing.pdf p55) See what that buys. With ordinary IP, two packets for the same destination take the same route from any given router, because they match the same prefix. With labels, an ingress router can place them on different prepared paths. The original motive for MPLS included faster lookup. Today, traffic engineering is the bigger reason.

[01:41:28] (lec10-routing.pdf p54) Remember what a label path is, and what it is not. It's prepared forwarding state. It doesn't by itself reserve bandwidth, and it doesn't make delivery reliable. Something must still decide what state to install, and that's the control plane again.

[01:41:48] (lec10-routing.pdf p54) Back to our laptop's packet. At every router on the way to the server, it now finds a table entry, built from a shared map, from neighbors' distances, or from paths. Where MPLS is in use, it may even carry a label for part of the way. The packet itself never knew any of this happened.

[01:42:11] (lec10-routing.pdf p54) A label alone doesn't reserve anything. It's just how a router finds the next step. Reserving capacity takes signaling, and not every MPLS deployment uses it.

[01:42:25] (lec10-routing.pdf p56) Change the question. R2's own table reuses label 17 for a totally different path, on another interface. And a packet with label 99 arrives at R2, where no entry exists.

[01:42:41] (lec10-routing.pdf p56) Is reusing 17 a conflict? And can the router just fall back to searching the label space for the packet with 99?

[01:42:58] (lec10-routing.pdf p56) Reuse isn't automatically a conflict, because labels are local, and each entry's scope is defined by its table. Different routers routinely reuse the same number. A label with no matching state has no installed instruction, so it has no valid forwarding action. State has to exist before it can be used. And that raises this chapter's biggest question. We've treated every table as correct and complete. What really happens in the seconds after a link fails?

## Chapter 11: Lecture 11: Convergence

### 11.1 When a link fails

[01:43:33] (lec11-convergence.pdf p4) A backhoe cuts a fiber between two routers. A moment before, every table was correct. A few seconds later, every table will be correct again. So what happens to our laptop's packets during those few seconds? The answer shows that correct before and correct after does not mean safe in between.

[01:43:59] (lec11-convergence.pdf p4) Picture our laptop's video call, running happily through R1 and R2. The packets keep coming every few milliseconds, whether the tables are ready or not. So a failure isn't an abstract event. It happens underneath traffic that's already moving.

[01:44:19] (lec11-convergence.pdf p4) First, what kinds of change are we talking about? Some are planned: maintenance that shuts down a link, or traffic engineering that changes a weight. Others aren't: a fiber cut, a power failure, or crashing software. Keep this separate from a different problem we'll reach later. A new route to the same location is a routing change. A host moving to a new location is mobility. Here, the destination stays put, and the network underneath it changes.

[01:44:55] (lec11-convergence.pdf p5) First, how does anyone even find out? Sometimes the hardware reports a dead link. Often routers exchange periodic hello messages, and declare a neighbor dead after a few are missed. That leaves a real tension. A short timer finds failures quickly, but it costs more traffic and processing, and it can raise false alarms, since a delayed hello looks exactly like a dead neighbor. A long timer is calm, and slow.

[01:45:27] (lec11-convergence.pdf p7) Detection is just the start, and it's local. Everybody else must then be told. Routing convergence is the whole transition, and it has four stages. Detect the change. Spread the news. Compute new routes. Install them in forwarding tables. If those take 30, 10, 5, and 15 milliseconds in sequence, the total is 60 milliseconds. Real stages can overlap, and each router's clock runs differently. But name the stages, before you blame the algorithm.

[01:46:07] (lec11-convergence.pdf p8) Watch the packets. A forwards traffic for D to B, and B forwards to D. The link from B to D fails. B knows, but A hasn't heard. A keeps sending to B, on its old and perfectly reasonable route. B has nothing usable, and those packets vanish. That's a forwarding blackhole. Note that A has not computed anything wrong. It's just working from old information.

[01:46:38] (lec11-convergence.pdf p9) B computes a new route for D. It goes back through A, then C, then D. And B installs that first, while A still points to B. So look at what happens now. A sends the packet to B. B sends it back to A. They bounce it between them. The old configuration had no loop. The new configuration has no loop. The mix of the two does. This is a transient forwarding loop. It isn't specific to any one protocol, and it can happen with link state, whenever routers install their changes at different times.

[01:47:19] (lec11-convergence.pdf p10) What does IP's TTL do here? It eventually kills the looping packet, but it doesn't save it, and until then, the loop eats up link capacity. Other packets may arrive out of order when old and new paths have different delays. So an application can suffer, even if a perfectly good alternate path exists the whole time.

[01:47:44] (lec11-convergence.pdf p11) To improve convergence, work stage by stage. Detect faster. Send control messages promptly. Compute incrementally. Install changes efficiently. And keep the principle in mind: a faster processor cannot make up for waiting minutes to declare a neighbor dead. Find the slowest stage first.

[01:48:10] (lec11-convergence.pdf p11) A tempting thought: both the old tables and the new tables are correct, so no harm done. But correct before and after protects nobody in between. Packets can vanish or loop during the transition.

[01:48:26] (lec11-convergence.pdf p9) Change the install order. Same failure, same routers, but this time A installs its new route first, and goes through C directly. Then B installs its route, by way of A.

[01:48:41] (lec11-convergence.pdf p9) With that order, is there a loop? Is there still a blackhole, at any moment?

[01:48:55] (lec11-convergence.pdf p9) No loop forms, because A no longer sends to B. Traffic from A goes straight to C and D. Packets that reach B in the gap before it installs can still be lost, so B's own blackhole lasts until it updates. Ordering changes which disruption you get. These problems come from timing, and they pass quickly. But one protocol family can make things far worse: nobody gets told the truth for a very long time.

### 11.2 Counting to infinity

[01:49:26] (lec11-convergence.pdf p12) Distance vector routers believe the numbers their neighbors tell them. When a link gets cheaper, that's wonderful. When a link fails, it's a disaster, and the reason is not obvious. Why should good news travel fast, while bad news crawls?

[01:49:46] (lec11-convergence.pdf p14) Start with good news. A link cost drops. The router attached to it sees a better distance, tells its neighbor, who sees a better distance too, and tells the next. The improvement spreads in a couple of exchanges, and everyone stops. A real, better path exists, so every update is true.

[01:50:10] (lec11-convergence.pdf p16) The bad news, on this tiny chain. Y reaches X directly, at distance 1. Z reaches X through Y, at distance 2. And there is no other route to X in this network at all. Now cut the link between X and Y. X is gone. Y knows immediately. What should it do? It looks at what its neighbors have advertised, and it sees Z saying, I can reach X at distance 2.

[01:50:42] (lec11-convergence.pdf p17) The trap. Y has no way of knowing that Z's path runs through Y itself. A bare number hides that. So Y believes it. Z's 2 plus a link of 1 makes 3, and Y now routes to X through Z. Y tells Z the news: I'm at 3. Z depends on Y, so Z updates: 3 plus 1 is 4. Z tells Y. Y updates: 5. Then Z: 6.

[01:51:15] (lec11-convergence.pdf p17) Stop and see what those numbers mean. There is no path to X at all. Yet each router is confident. They point at each other, and their traffic bounces between them, while the numbers creep up, until they reach whatever the protocol treats as infinity. No new links appeared. The routers are slowly unlearning something false. This is called count to infinity. It's information feedback, not any physical growth in the network. And a cost increase can trigger the same counting, even if a real but expensive alternate exists. They just count up until the alternate wins.

[01:51:59] (lec11-convergence.pdf p19) One crude fix is to make infinity small. RIP treats 16 as unreachable, leaving 1 through 15 as usable metrics. Now the counting stops at 16, soon rather than never. But any network wider than 15 hops can't be represented. And the underlying problem has not gone anywhere. We only bounded it.

[01:52:25] (lec11-convergence.pdf p18) A better fix targets the actual lie. Go back to before the failure. Z's route to X goes through Y. So why would Z ever tell Y that it has a route to X? That information is useless to Y, and we've just seen that it's dangerous. Poison reverse says: if you route through a neighbor, tell that neighbor your distance is infinity. Z keeps its true route, and tells Y infinity. It can still tell its other neighbors the truth. So the advertisement is specific to each neighbor. It is not a command to delete anything.

[01:53:05] (lec11-convergence.pdf p18) Replay the failure. X and Y lose their link. Y checks its neighbors. Z says infinity. So Y knows it has nowhere to go, and it tells Z so. Z's only route was through Y, so Z drops to infinity as well. Done, in one quick exchange, with no counting.

[01:53:29] (lec11-convergence.pdf p15) See the counting itself with the slide's real numbers, on a slightly bigger network. X to Y costs 4, Y to Z costs 1, and X to Z costs 50. Y reaches X directly at 4, and Z goes through Y, at 5. Now suppose X to Y gets better, dropping to 1. Y's distance falls to 1, and it tells Z. Z computes 2. Z tells Y, and Y stays at 1. Done, in two exchanges.

[01:54:05] (lec11-convergence.pdf p17) Make it worse, raising X to Y from 4 to 60. Y compares a direct cost of 60 with Z's old claim of 5, through a link of 1, for a total of 6. It picks 6, through Z, not knowing that Z's 5 ran through Y. Z hears 6, and computes 7. Y hears 7, and computes 8.

[01:54:30] (lec11-convergence.pdf p17) They climb 2 at a time, while packets for X bounce between them. It only ends when going through Y costs more than Z's real direct link of 50. Then Z settles at 50, and Y at 51. That took more than twenty exchanges, for one changed number. Without the 50 link, it would never stop on its own.

[01:54:56] (lec11-convergence.pdf p17) Making infinity small feels like a fix. It isn't. It only bounds the counting, and it limits how wide the network can be. The underlying dependency is still there.

[01:55:10] (lec11-convergence.pdf p18) Is the problem solved? Add a third router to the loop. Now Y, Z, and W form a triangle, and they all reach X through Y. Z and W are each other's neighbors.

[01:55:26] (lec11-convergence.pdf p18) Z poisons its route toward Y. But what does Z tell W? Could W now give Y bad advice?

[01:55:42] (lec11-convergence.pdf p18) Z tells W the truth: distance 2. It doesn't route through W, so it has no reason to poison. W then thinks it has a path to X through Z, and it can tell Y. So a loop of three can still count up. Poison reverse handles the simple two-node case, not every cycle. What's the real issue? The number hides the path. So what if routers just sent the path? That's the fix BGP uses, and we'll see that even this doesn't make the trouble go away.

### 11.3 BGP that won't settle

[01:56:19] (lec11-convergence.pdf p25) Path vector carries the whole path, so a router can spot a loop at once, and count to infinity disappears. Does that mean convergence is solved? There are two remaining problems. It can be slow in a new way. And even worse, with some policies, it may never settle at all.

[01:56:42] (lec11-convergence.pdf p24) First, how do BGP neighbors notice that one of them has died? BGP runs over a TCP connection, and TCP alone won't tell you that an idle peer has vanished. So neighbors send keepalive messages. In the slide's example, a keepalive goes every 60 seconds, and the hold timer is 180 seconds. If nothing arrives for that long, the session is declared dead. Every route learned over it is then invalid. So just detecting one failure may take three minutes.

[01:57:19] (lec11-convergence.pdf p27) Suppose destination 0 disappears entirely. Follow AS 2 as the news spreads. It's been using the direct path, 2, 0. That gets withdrawn. But it remembers an alternative through AS 1: 2, 1, 0. It looks fine, it's loop-free, and it's false, since AS 1 simply hasn't heard yet. Then that's withdrawn too. So it tries 2, 3, 0, which is also stale. Next 2, 1, 3, 0, longer still. Only after all of those does it finally have no route. This is path exploration. Each candidate seems reasonable locally, and each fails in turn. Every step also causes more update messages.

[01:58:14] (lec11-convergence.pdf p28) Why doesn't that settle faster? Each router must first hear about the failure of what it's using, then choose its next best candidate, and advertise that. Those messages are limited by timers, so that routers aren't flooded with updates. So each wrong candidate can take a while to be discovered. Also, not every BGP change is a hardware failure. Import and export policy changes, resets of sessions, and persistent instability all make routes change too.

[01:58:50] (lec11-convergence.pdf p30) The deeper problem. Each network ranks paths by its own policy. Do those independent choices always fit together? To study this, there's a clean model called the stable paths problem. Each node has a ranked list of permitted paths to destination 0. A path is available only if the next hop is actually using exactly the rest of that path. A stable assignment gives every node its best available path, all at the same time.

[01:59:23] (lec11-convergence.pdf p31) Solve the instructor's instance. Node 3 has only one permitted path, 30, so it uses it. Node 1 prefers 130, and since 3 uses 30, that's available, so node 1 uses 130. Node 2 prefers 210, which requires node 1 to use 10. But node 1 uses 130, so that's unavailable, and node 2 falls back to 20.

[01:59:54] (lec11-convergence.pdf p31) Node 4 prefers 420, and node 2 does use 20, so 420 works. Node 5 allows only 5210. That needs node 2 on 210, which it isn't. So node 5 has no path, even though it's physically connected to node 2. The slide asks two questions. Will node 1 use a direct path? False. Does node 5 have a path? False.

[02:00:28] (lec11-convergence.pdf p32) That instance has exactly one solution. Others don't. Take two nodes, each preferring to reach the destination through the other. Node 1 likes 120 best, and node 2 likes 210 best. There are two stable outcomes. Node 1 goes through node 2, while 2 goes direct. Or the reverse. Which one you get depends on who speaks first. Same policies, same links, different result.

[02:01:02] (lec11-convergence.pdf p34) Three nodes in a ring. Each prefers the path through its clockwise neighbor, and each will otherwise go direct. Try to settle them. If node 1 goes direct, node 2 can use its favorite, through node 1, and so node 2 is not direct. Then node 3 can't use 320, and goes direct. But then node 1 can use 130, its favorite, and is no longer direct. That undoes node 2's choice. And round it goes. An exhaustive check of every assignment finds no stable solution at all. No link failed. Policies alone keep routes changing, forever. That's policy oscillation.

[02:01:51] (lec11-convergence.pdf p34) For our laptop, all of this shows up as a stall or a gap. Its video freezes for a moment, and then recovers. The laptop did nothing wrong, and neither did its server. The network was changing its mind, or couldn't settle it.

[02:02:09] (lec11-convergence.pdf p34) The trap with path exploration. A path with no AS loop can still be stale. No loop is a much weaker claim than, this path is still available now.

[02:02:22] (lec11-convergence.pdf p34) Change one line of policy. Node 3 decides it will no longer prefer the path through node 2. It now ranks going direct first, with 320 second.

[02:02:36] (lec11-convergence.pdf p34) Does that single change produce a stable solution? Work it out starting from node 3.

[02:02:57] (lec11-convergence.pdf p36) Yes. Node 3 uses 30, and never moves. So node 1's favorite, 130, is always available, and node 1 uses it. Node 2 then can't use 210, and so it goes direct, on 20. Everyone's happy, and nothing changes. One local preference broke the cycle. So the trouble isn't BGP's messages, it's the combination of rankings. Then what real-world force keeps the Internet's policies from forming these cycles? The answer is money. Let us see how BGP really works, and how business relationships shape it.

## Chapter 12: Lecture 12: BGP

### 12.1 What BGP carries

[02:03:41] (lec12-bgp.pdf p3) Our laptop's packet to the web server has so far crossed two friendly routers. On the real Internet, it would cross networks owned by companies that compete with each other, each one keeping its internal design private, and each one with its own idea of what a good route means. How can those rivals still cooperate well enough to deliver a packet? There's exactly one protocol doing this job across the whole planet, and we need to see what it actually says.

[02:04:15] (lec12-bgp.pdf p3) Our laptop's server sits in a different network from the laptop, run by a different company. Everything we've built so far works inside one organization. So who tells R2's network that the server's prefix even exists, and why would they agree to carry it?

[02:04:34] (lec12-bgp.pdf p3) A little context. The Internet's interdomain routing protocol is BGP, and it's been in use, in revised versions, since the early days of the commercial Internet. It's a path-vector protocol, the very idea from chapter 6. Now we can fill in how it really works.

[02:04:56] (lec12-bgp.pdf p4) The unit of cooperation is the autonomous system, or AS. That's a set of networks under one routing administration, identified by a number. A university, an Internet provider, or a content company can each be an AS. Inside, it may run many routers, using OSPF or IS-IS, and that's nobody else's business. From the outside, we draw it as a single cloud. This is an abstraction with a price, which we'll get to in a moment.

[02:05:31] (lec12-bgp.pdf p5) BGP, the Border Gateway Protocol, is what those clouds speak to each other. Two routers open a TCP connection on port 179, called a session. First they exchange all their active routes. After that they send only changes: announcements of new routes, and withdrawals of old ones. That makes it an incremental protocol. It's also prefix based, so what it advertises is reachability to a block of addresses, like 203.0.113.0/24, not to individual machines.

[02:06:13] (lec12-bgp.pdf p7) What exactly is a BGP route? It's a prefix, plus attributes. Two matter most right now. AS PATH is the list of autonomous systems the route has passed through. NEXT HOP says which IP address to send toward. Watch how the path grows. AS 300 owns the prefix, and it tells AS 200 the path is just 300. AS 200 adds itself, and tells AS 100 that the path is 200, 300.

[02:06:48] (lec12-bgp.pdf p8) Inside that list is our loop check from before. A receiving AS looks for its own number, and if it's there, the route is rejected. That handles one kind of consistency. We've already seen that it doesn't prevent path exploration or policy oscillation.

[02:07:08] (lec12-bgp.pdf p10) The price of the abstraction. Is a shorter AS path a shorter route? Not necessarily. Here are two options. One crosses 2 ASes, but each contains a long chain of routers. The other crosses 3 ASes, each with only one or two routers. Measured in router hops, the 3 AS path is the shorter of the two. And it says nothing at all about delay. AS path length counts organizations, not distance.

[02:07:43] (lec12-bgp.pdf p10) Don't read too much into AS path length. It counts networks, not routers. It says nothing about latency or capacity, and prepending can make it artificial.

[02:07:57] (lec12-bgp.pdf p8) You try. AS 200 gets an offer of 300, 500. It passes that along to AS 100, and AS 500 is also a neighbor of AS 100. Suppose AS 100 then re-advertises its path to AS 500.

[02:08:18] (lec12-bgp.pdf p8) What is the path list when it reaches AS 500? And what will AS 500 do with it?

[02:08:32] (lec12-bgp.pdf p8) AS 500 receives 100, 200, 300, 500. It sees its own number at the end, and it rejects the route. Notice one thing we still haven't said: when AS 100 has several acceptable routes, how does it pick? And who decides which neighbors hear about the choice? That isn't physics, and it isn't shortest paths. It's policy.

### 12.2 Import and export

[02:09:02] (lec12-bgp.pdf p12) A neighbor hands you a route. Do you have to believe it? Do you have to use it? If you use it, must you tell everyone else? With BGP, the answer to all three questions is no. Those are three separate decisions, and getting them apart is the key to the whole protocol.

[02:09:24] (lec12-bgp.pdf p13) The pipeline in every BGP router. Routes arrive from neighbors. Import policy filters them, and may change their attributes. Best-route selection picks one route per prefix for use. That route goes into forwarding. Then export policy decides, separately for each neighbor, what to advertise. Because the stages are separate, a route rejected at import never becomes a candidate. A route suppressed at export can still be the one you use yourself.

[02:10:00] (lec12-bgp.pdf p15) Import first. Why would you ever reject a route? Say your customer owns one prefix, and suddenly announces a route to a big video site. That's either a configuration mistake, or an attack. Believing it would pull the world's traffic into your customer's network. So on a session to a customer, a network commonly accepts only the prefixes that customer actually holds. An advertisement is data to evaluate, not an order.

[02:10:34] (lec12-bgp.pdf p14) Import can also attach a value called local preference. It's a number used only inside your own AS, and higher is better. It's checked before anything else, so it directly states your own ranking. For example, you might set 100 on routes from a customer, and 90 on routes from a peer, because customers pay you, and carrying traffic to them earns money. Compare. A customer route with local preference 100 and an AS path of 4, against a peer route with local preference 90 and an AS path of 2. The customer route wins. Length is never even looked at.

[02:11:17] (lec12-bgp.pdf p16) The other end of the pipeline. Export policy decides what each neighbor gets to hear. Why not tell everyone everything? Because telling a neighbor about a route is an offer: send your traffic through me, and I'll carry it. Advertising a route is promising to do work. So a network can use a route itself, while deliberately keeping it from a neighbor. Using a route and offering transit are different acts.

[02:11:48] (lec12-bgp.pdf p18) Export can also change how a route looks. Suppose you have two links to the Internet, and want incoming traffic on just one of them. You can't control anybody else's decision. But you can make one option look worse. AS path prepending repeats your own number. Instead of announcing 300, you announce 300, 300, 300 over the backup link. Remote networks comparing path lengths will tend to choose the other link. Tend to, because prepending can't force anything. A remote network's local preference is checked first, and it could still ignore you.

[02:12:32] (lec12-bgp.pdf p18) Keep these two tools straight. Local preference ranks routes within your own AS, and it controls your outgoing traffic. Prepending changes what others see, so it only influences your incoming traffic. One is a decision. The other is a suggestion.

[02:12:53] (lec12-bgp.pdf p19) Where do all these policies live? Administrators write them, per neighbor, in router configuration. That's a lot of manual work, spread over many routers and many people, and mistakes do happen. A configuration error can be visible across the entire Internet.

[02:13:15] (lec12-bgp.pdf p19) A common mistake is to weigh these numbers against each other. There's no trade between preference and path length. Preference is compared first, and length matters only if preference ties.

[02:13:29] (lec12-bgp.pdf p14) A situation. Network A prepends heavily on its link to provider P, hoping traffic will arrive by way of provider Q instead. But a far-off network, Z, assigns a high local preference to routes learned through P.

[02:13:47] (lec12-bgp.pdf p18) Which way does Z's traffic arrive at A? And did the prepending do anything at all?

[02:14:01] (lec12-bgp.pdf p18) It arrives through P, the path A was trying to discourage, because Z compares local preference first, and never reaches the length comparison. Prepending may still influence others who have tied preferences. So that's the outside view of an AS. But an AS isn't really one node. It's a set of routers with their own geography. How do they agree on what to do?

### 12.3 Inside an AS

[02:14:29] (lec12-bgp.pdf p21) We've been drawing each AS as a dot. But a large provider has hundreds of routers across a continent, and it may hear about the same destination at several different border routers. How do all its internal routers learn about that, and how does each one pick an exit?

[02:14:49] (lec12-bgp.pdf p22) A BGP session between different ASes is called eBGP, for external. A session between routers within the same AS is iBGP, for internal. Here's the flow. Border router R1 learns a route over eBGP. It passes this along to R2 and R3 over iBGP. Now all of them know the route. Note that internal routers don't add their AS number again as the update moves around inside.

[02:15:21] (lec12-bgp.pdf p23) And iBGP does not replace the internal routing protocol. It says that a destination is reachable through a certain exit. But it doesn't say how to get across your own network to that exit. That's still the job of OSPF or IS-IS. BGP and the IGP solve two halves of one problem.

[02:15:44] (lec12-bgp.pdf p29) How those halves are joined. BGP says: 203.0.113.0/24 has next hop 192.0.2.9. But that router may be several hops away. So the router looks up 192.0.2.9 in its internal routes, and finds it goes through neighbor 198.51.100.2 on port 3. It combines the two, and installs: 203.0.113.0/24 goes through 198.51.100.2 on port 3. A BGP next hop isn't necessarily a directly connected neighbor. It has to be resolved first.

[02:16:37] (lec12-bgp.pdf p24) Now the decision process can be stated in full, in the lecture's simplified order. Highest local preference. Then shortest AS path. Then lowest internal cost to the exit. Then a tie break. Compare in order, and stop as soon as one route remains. These are not added into a score. There's no formula that combines them.

[02:17:06] (lec12-bgp.pdf p26) Try three routes for one prefix. A has local preference 140, length 4, and exit cost 50. B has 100, length 2, and cost 5. C has 100, length 2, and cost 1. With all three available, A wins immediately on preference, despite being the worst by every other number. Withdraw A. B and C tie on preference, and tie on length, so internal cost decides: C wins. Now shorten B's path to length 1. B beats C at step two, and its higher exit cost never gets compared.

[02:17:49] (lec12-bgp.pdf p25) That third step has a nickname: hot-potato routing. When outside attributes tie, hand the traffic off at the nearest exit, and spend as little of your own network as possible. Picture a network with exits on the west and east coasts. A router with internal costs 4 and 9 picks west. A router on the other side, with costs 12 and 3, picks east. Each one minimizes its own carrying cost. And so the return path, chosen by a different network with its own hot potatoes, may take a different route. Internet paths are often asymmetric for just this reason.

[02:18:33] (lec12-bgp.pdf p30) Does every router need all those routes? No. A customer with a single provider has only one way out. It can use a default route: a slash 0, matching everything, pointing at the provider. Any longer prefix beats it. So a stub network, or an internal router at the edge, can hold a very small table. Full tables belong where real choices exist, not everywhere.

[02:19:03] (lec12-bgp.pdf p30) The classic confusion. A BGP next hop isn't necessarily the neighbor you hand the frame to. It can be several routers away, so it has to be resolved through internal routing.

[02:19:19] (lec12-bgp.pdf p25) Change the costs. Internal maintenance raises router R's cost to the west exit from 4 to 11. Its east cost stays at 9. Nothing outside the AS has changed.

[02:19:34] (lec12-bgp.pdf p25) Does R's exit change? And does some neighbor network now see traffic it wasn't seeing before?

[02:19:49] (lec12-bgp.pdf p25) Yes. R now prefers east, at 9. Its traffic moves to a different exit, and possibly to a different neighbor network. An internal change shifted traffic outside the AS. That's the coupling between BGP and the internal protocol. We've now covered how the decision works. But why do networks set these preferences in the first place? Because each link between two networks has a contract, and someone pays.

### 12.4 Money shapes paths

[02:20:22] (lec12-bgp.pdf p34) Networks are businesses. Carrying traffic costs money, and some of it pays and some doesn't. If you ran a network, whose traffic would you carry for free? Whose routes would you repeat? Those two business questions end up explaining most of Internet routing.

[02:20:43] (lec12-bgp.pdf p35) There are two main relationships. In a customer-provider link, the customer pays the provider for connectivity to the rest of the Internet. We draw the arrow pointing from customer up to provider. In peering, two networks exchange traffic, typically without payment, but only for themselves and their customers. A peer isn't offering you transit to the world. It's only offering you what's below it.

[02:21:13] (lec12-bgp.pdf p41) From these contracts comes one question that decides every export. Would this make me carry traffic between two networks, when neither is my customer? If a route came from a customer, or it's my own, then I tell everyone, because traffic toward it earns me money. If it came from a peer or a provider, I tell only my customers. Telling a provider about my peer's route would invite my provider to send traffic through me, to my peer, for free, while I pay for it. So read the table. Own and customer routes go everywhere. Peer and provider routes go only to customers.

[02:21:56] (lec12-bgp.pdf p36) Those contracts stack up into a structure. At the top are Tier 1 providers, with no upstream provider at all, connected to each other as peers. Below them are other providers, which sell transit to customers, but must buy it from someone. At the bottom are stub ASes, which provide no transit, and those are the vast majority. And this graph has a key property. It's directed and acyclic. If u is a customer of v, and v is a customer of w, then w isn't a customer of u. Remember that when we come to stability.

[02:22:37] (lec12-bgp.pdf p43) Those exports have a visible consequence in the data path. A permitted path climbs up through customer to provider links, crosses at most one peer link, and then descends through provider to customer links. It's up, peer, down. It's called valley free. Going down and then back up would be a valley: some customer would be carrying traffic between its two providers, paying both for the privilege. Nobody signs up for that.

[02:23:09] (lec12-bgp.pdf p46) Classify the instructor's paths, reading in the direction data travels. 1, 2, d: down, down. Valid. 7, d: up. Valid. 5, 8, d: 8 is 5's customer, so that's down, then up. A valley. Invalid, since 8 would carry traffic between its providers. 6, 4, 3, d: up, peer, down. Valid. 8, 5, d: up, peer. Valid. 6, 5, d: peer, peer. Invalid, because a path can have only one peer crossing. And 1, 4, 3, d: down, peer, down. Invalid, because the peer crossing comes after descending.

[02:24:06] (lec12-bgp.pdf p47) Look at two of those again. 5, 8, d is invalid. And 8, 5, d is valid. They use nearly the same networks, in a different direction. So direction matters, and the set of nodes alone tells you nothing. Build the relationship sequence, and read it, rather than memorizing node numbers.

[02:24:31] (lec12-bgp.pdf p39) The payoff, connecting to the oscillating ring from last chapter. Gao and Rexford showed that three commercial habits are enough for stability, under their model. One: the customer-provider hierarchy has no cycles, so nobody is their own provider's provider. Two: prefer customer routes over peer and provider routes. Three: follow the export rule we just saw. Why does the bad gadget disappear?

[02:25:02] (lec12-bgp.pdf p39) Its cycle needs each network to prefer a route through its neighbor, around a ring. Under these rules, that ring of preferences can't form. Those are sufficient conditions in the model. They aren't a claim that every BGP deployment follows them, or that every stable network must. Still, it's striking. No one coordinates globally. Each business pursues its own interest, and the system tends to settle.

[02:25:34] (lec12-bgp.pdf p39) Look at the whole path of our laptop's packet. It climbs from the laptop's provider, perhaps crosses one peer link, and descends to the server's provider. Contracts set that shape. The shortest path on a map had very little to do with it.

[02:25:53] (lec12-bgp.pdf p39) A short path in the drawing isn't necessarily a usable one. If export policy never advertised it, no traffic will follow it, however connected it looks.

[02:26:06] (lec12-bgp.pdf p41) A business decision. AS A has a peer P, a provider U, and a customer C. It learns a route from P. And it learns another route from its customer C.

[02:26:20] (lec12-bgp.pdf p41) Who hears about P's route from A? Who hears about C's route?

[02:26:35] (lec12-bgp.pdf p41) P's route goes only to customer C. Telling U would have A carrying traffic between its provider and its peer. C's route goes to everyone: U, P, and C itself has it already. That's exactly the reachability A is being paid to spread. So far, every packet has had one destination. But what if one address should mean several servers? Or what if a thousand receivers all want the same stream? Our next chapter changes who a destination is.

## Chapter 13: Lecture 13: Anycast and multicast

### 13.1 One address, many servers

[02:27:11] (lec13-multicast.pdf p5) Our laptop has been talking to one server. But a popular service runs in many locations. DNS could return different addresses, but what happens if one of those servers fails? The laptop's cache keeps handing out the dead address until the TTL runs out. Could one single address lead to several servers, so a failure needs no new DNS answer at all?

[02:27:40] (lec13-multicast.pdf p5) So far, our laptop has sent to exactly one server. But when it looks up a popular name, which of a thousand servers should answer? And when it joins a live stream, what if a million other laptops want the same bits? The destination is about to stop meaning one machine.

[02:28:02] (lec13-multicast.pdf p4) See the limit first. A DNS answer may hold several A records, for load balancing and failover, each one valid for 300 seconds. If a server fails, clients can hold on to its address for that long. A very low TTL puts extra load on DNS, and browsers may cache addresses regardless. And what if the DNS server itself is the thing that fails? We can't use DNS to fail over DNS.

[02:28:34] (lec13-multicast.pdf p7) It can, and it takes no new protocol. Give two server instances the same address, 10.0.0.1, and let both locations announce it into routing. Routers simply see two routes to one destination. Router 1's table lists 10.0.0.1 through router 2 at distance 1, and through router 3 at distance 2. It chooses the closer one, just as it would for any route. That's IP anycast. One destination, delivered to one selected instance.

[02:29:12] (lec13-multicast.pdf p11) Instance A fails, and its route is withdrawn. The client does nothing. It keeps sending to the same address. Router 1 falls back to the remaining route, and packets now reach instance B. There's no new DNS answer, and no client change. But failover isn't instant. It still waits for health detection, and routing convergence. And ordinary routing knows nothing about server load, or whether the program behind a live route is actually healthy.

[02:29:48] (lec13-multicast.pdf p9) Here's the rule. Anycast means one of many, and routing picks which one. DNS still says just one thing, www.server.com is 10.0.0.1, and that answer stays true. Be aware that the slide's slash 32 is an internal toy example. Whether the wider Internet accepts a prefix that specific depends on routing policy.

[02:30:17] (lec13-multicast.pdf p9) The slide's warning is easy to overread. Anycast isn't banned for TCP. The real issue is that a flow might shift to an instance without its connection state.

[02:30:30] (lec13-multicast.pdf p14) Use anycast for something long-lived. A client has an open TCP connection to instance A. Routes shift, though nothing failed, and the next packet is delivered to instance B. **Clarification:** The issue is lost connection state, not a blanket incompatibility with TCP (lec13 p14; RFC 4786).

[02:30:45] (lec13-multicast.pdf p14) What does instance B do with that packet, and why?

[02:30:57] (lec13-multicast.pdf p14) B has never heard of this connection. It has no state for it, so the connection can break. That's the real meaning of the slide's warning. The problem is lost connection state, and anycast isn't flatly incompatible with TCP. Stable routing and careful service design make it workable. In fact, the DNS root servers we met earlier are deployed this way: 13 identities, with many anycast instances. Anycast picked one receiver out of many. Next, what if we want all of them? **Clarification:** The issue is lost connection state, not a blanket incompatibility with TCP (lec13 p14; RFC 4786). **Clarification:** 13 refers to root identities A to M, each deployed as many instances (lec09 p31).

### 13.2 Who wants the stream?

[02:31:35] (lec13-multicast.pdf p16) A source wants to send one 10 megabit per second stream to three receivers. All three sit behind the same first link. Must that link really carry three identical copies? And how would the network even know who wants the stream?

[02:31:53] (lec13-multicast.pdf p22) The simple answer is iterated unicast. Just send a separate copy to each receiver. It needs no network support at all. But on the shared link, that's 3 times 10, or 30 megabits per second, all carrying the same bits.

[02:32:13] (lec13-multicast.pdf p22) Scale it up. A one megabyte file sent separately to 100 receivers makes the sender transmit 100 megabytes. If every copy crosses the same upstream link, that link carries all 100.

[02:32:29] (lec13-multicast.pdf p18) IP multicast does better. The source sends one copy, addressed to a group, and routers replicate it only where paths diverge. The shared link carries just 10 megabits per second. The saving is on the shared edges. There's still forwarding work at each branch. And notice the difference from anycast. Anycast reaches one of many. Multicast reaches all who are interested.

[02:33:00] (lec13-multicast.pdf p19) What goes in the packet? The sender keeps its ordinary source address. The destination is a group address, drawn from 224.0.0.0/4. That address names no single machine, only an audience. A sender doesn't have to be a member. And the group's membership can change at any time.

[02:33:26] (lec13-multicast.pdf p19) A concrete example. A sender at 192.0.2.10 sends to group 239.1.1.1, and two receivers join that group. The packet's source stays 192.0.2.10, and its destination is 239.1.1.1. The source never becomes the group address.

[02:33:54] (lec13-multicast.pdf p22) What if routers don't support multicast? Overlay multicast builds the distribution tree among the end hosts themselves, using ordinary unicast. Each host receives the stream, and forwards it to a few others. It needs no router support. But overlay paths can cross the same physical link repeatedly, and forwarding uses up the hosts' upload capacity.

[02:34:22] (lec13-multicast.pdf p22) Picture it as a tree of hosts. The source sends to two peers, and each of them sends to two more. Seven recipients fit in three levels, and no router needs to know anything about the group.

[02:34:37] (lec13-multicast.pdf p28) Who's interested? IGMP handles this on the local network, between hosts and their directly attached router. The router sends a query: any members out there? Hosts reply with reports. Here's a clever trick. H1 and H2 both want group G. Each picks a random delay, say 2 seconds and 6 seconds. H1's timer fires first, and it sends its report to the group itself. H2 hears the report, and cancels its own. Why? Because the router only needs to know that someone on this LAN wants G, not who, or how many. In version 1 there's no leave message. Membership simply expires when reports stop.

[02:35:28] (lec13-multicast.pdf p27) The slides speak loosely here, so let's be exact. In version 1, queries go to the all-hosts group, and a report goes to the group being reported. That's how H2 hears H1's report. Both are limited to the local network with a TTL of 1. **Clarification:** In v1, queries go to all hosts and a report goes to the group being reported (lec13 pp27, 31; RFC 1112).

[02:35:49] (lec13-multicast.pdf p32) Version 2 adds an explicit leave. When a host leaves, can the router stop forwarding at once? No. Another host on the LAN may still want the group. So the router sends a group-specific query to check. If H2 still cares, its report keeps the branch alive. Version 2 also adds querier election. Version 3 adds source filtering, so a host can say: I want group G, but only from source S.

[02:36:23] (lec13-multicast.pdf p33) A timer detail, with a clarification. The slide computes a timeout as 2 times the sum of 125 and 10, which gives 270 seconds. The standard's default formula, in RFC 2236, is 2 times 125, plus 10, which gives 260 seconds. If a question supplies the slide's formula, use it, and say so. Just don't quietly swap one for the other. **Clarification:** The slide computes 270 s; RFC 2236's default formula gives 260 s (lec13 p33).

[02:36:57] (lec13-multicast.pdf p33) Finally, what about the switch? An ordinary switch floods multicast out every port. IGMP snooping lets it listen in on these membership messages, and deliver only to ports with interested hosts. So keep the scope clear. IGMP is about one local network. It doesn't build the tree between routers.

[02:37:23] (lec13-multicast.pdf p33) Say only one port has a receiver for a group. A snooping switch sends that group's traffic toward that port, and toward its router ports, rather than every access port. This is separate from unicast MAC learning, because it comes from reading membership messages.

[02:37:42] (lec13-multicast.pdf p33) Keep the scope straight. IGMP tells the last router which groups are wanted on its LAN. It doesn't compute the tree between routers. That's a multicast routing protocol's job.

[02:37:58] (lec13-multicast.pdf p30) Change the numbers. A 5 megabit stream, three receivers behind one shared link, with report delays of 2, 5, and 8 seconds.

[02:38:10] (lec13-multicast.pdf p30) What's the load on the shared link, with unicast versus multicast? And how many reports does the router actually hear?

[02:38:33] (lec13-multicast.pdf p30) Unicast loads the link with 15 megabits per second. Multicast with 5. And the router hears only one report, at 2 seconds, because the others suppress theirs. So local interest is known. But how does the data cross many routers, to reach all those interested networks? We need a tree. And it turns out the word tree can mean several different things.

### 13.3 Choosing a tree

[02:39:02] (lec13-multicast.pdf p36) To deliver to many networks, routers need a tree. But we've already met one tree in spanning tree, and another in Dijkstra's. Are they the same? What does best even mean for a tree? And should every sender get its own tree, or should they all share one?

[02:39:22] (lec13-multicast.pdf p36) First, a split. A source-based tree is rooted at one sender, so state is kept per source and group, written S comma G. A shared tree is used by all senders in the group, written star comma G. A shared tree needs less state. Source trees can give shorter paths. So we're trading memory against path quality.

[02:39:48] (lec13-multicast.pdf p37) Next, objectives. A minimum spanning tree connects all nodes with the smallest total edge cost. There are two classic ways to find one. Prim's algorithm grows one tree outward, always adding the cheapest edge that crosses from the tree to a node outside. Kruskal's algorithm sorts all edges, and adds each one unless it would create a cycle. Try this triangle: A to B is 1, B to C is 1, and A to C is 1 point 5. Both algorithms choose A B and B C, for a total of 2.

[02:40:26] (lec13-multicast.pdf p37) Ask a different question. What's the shortest way from A to C? It's the direct edge, at 1 point 5, which isn't even in that tree. Dijkstra's tree from A would use it. So three things share the word tree. STP makes layer 2 forwarding loop-free. An MST minimizes total edge cost. A shortest path tree minimizes distance from one source. Same word, different objectives. **Clarification:** STP, shortest-path trees, and MSTs have different objectives.

[02:40:59] (lec13-multicast.pdf p38) One more design: core-based trees. Pick one router as the meeting point, called the core. Each receiver's router sends a join toward the core, and that request stops as soon as it hits a router already on the tree. Traffic then flows along those branches. It's simple and uses little state. But the core could become a hot spot, and paths may take a detour through it.

[02:41:27] (lec13-multicast.pdf p38) The sharing. Receiver routers A and B both join toward the core, and their paths merge at M. So the branch from the core to M carries one copy, and M replicates it toward the two receivers.

[02:41:42] (lec13-multicast.pdf p38) These algorithms look alike, and they aren't. Dijkstra accumulates distance from a source. Prim just picks the cheapest edge reaching the growing tree. The resulting trees can differ.

[02:41:58] (lec13-multicast.pdf p37) Change one cost. Make the direct A to C edge cost 0 point 5.

[02:42:05] (lec13-multicast.pdf p37) What's the minimum spanning tree now, and its total cost? And what's the shortest path tree from A?

[02:42:27] (lec13-multicast.pdf p37) The MST takes A C at 0 point 5, plus one of the edges of cost 1, for a total of 1 point 5. There's a tie, so either A B or B C works. From A, the shortest path tree uses A C and A B. So this time the two objectives can coincide, on one of the valid MSTs. They just don't have to. Real multicast protocols don't compute a global MST. They use something cheaper, already sitting in every router: the unicast routing table.

### 13.4 RPF and PIM

[02:43:04] (lec13-multicast.pdf p40) A router receives a multicast packet. If it floods the packet out every port, loops and duplicates will multiply, and we saw how badly that ends on Ethernet. How can a router decide whether to accept a packet, without any tree having been computed?

[02:43:23] (lec13-multicast.pdf p40) An elegant trick. Look at where the packet came from, and ask: if I were sending a packet back to this source, which port would I use? If the packet arrived on that port, it probably came along the shortest path. Accept it, and forward it out the other ports. If it arrived anywhere else, it's a duplicate that wandered around another branch. Drop it. That's reverse path forwarding. Say router X reaches source S through port 1. A packet from S arriving on port 1 passes. A copy arriving on port 3 fails.

[02:44:06] (lec13-multicast.pdf p41) RPF alone still sends data everywhere, as a broadcast with no duplicates. Let's narrow it. Truncated reverse path broadcasting skips a leaf LAN when IGMP says no members exist there. That removes only the last hop. Reverse path multicasting goes further. If a router has no local members, and none of its downstream routers want the data, it sends a prune upstream. Prunes propagate, so entire uninterested subtrees drop out.

[02:44:41] (lec13-multicast.pdf p44) PIM, protocol independent multicast, is the standard router protocol. It's called independent because it reuses whatever unicast routing is available. PIM dense mode is the approach we've just seen. Flood, then prune. Everything is forwarded unless a branch opts out. That's sensible if most networks want the data, but wasteful if very few do. Prunes also expire, so the flooding comes back periodically.

[02:45:14] (lec13-multicast.pdf p46) When receivers are rare, we flip the default. In PIM sparse mode, nothing flows until someone asks. Everyone agrees on a meeting point for the group, called the rendezvous point, or RP. A receiver's designated router sends a star comma G join toward the RP, creating a shared tree. Data then flows only along the branches that joined. The slide's phrase, CBT, source based, is shorthand. What actually happens is that sparse mode starts with this shared tree. **Clarification:** Sparse mode starts with a shared (*,G) RP tree and may switch to (S,G) (lec13 p45; RFC 7761).

[02:45:51] (lec13-multicast.pdf p47) A source appears. Its designated router doesn't know the receivers. It only knows the RP. So it wraps the first data packets in a PIM Register message, and unicasts those to the RP. That's encapsulation again. The RP unwraps them, and sends them down the shared tree. Then the RP can set up native forwarding from the source, so that encapsulation is no longer needed.

[02:46:21] (lec13-multicast.pdf p47) Why wrap it at all? The source's router knows only the RP, and the RP hasn't built a path back yet. So Register is a bootstrap. The RP can unwrap each packet and send it down the shared tree, while native forwarding toward the source is being set up. A Register is not a join, and it's not a host's IGMP report.

[02:46:47] (lec13-multicast.pdf p49) But there's a problem: the RP might be far out of the way. Say source to RP costs 8, RP to receiver costs 7, and the direct path costs only 4. The receiver's router can now join toward the source, using S comma G. Once data arrives on the new path, it prunes this source from the RP branch. The cost drops from 15 to 4, a saving of 11. The group address stays the same. This is called SPT switchover. Start with a shared tree for easy discovery, then optimize.

[02:47:27] (lec13-multicast.pdf p50) There are two axes. Dense mode says: forward by default, and prune. Sparse mode says: send nothing until joined. And on any tree, RPF checks the upstream direction, while pruning trims the downstream outputs. IGMP tells the last router who is interested, and PIM connects the routers.

[02:47:52] (lec13-multicast.pdf p50) Set the two modes side by side. Dense mode starts broad, and shrinks. It needs no meeting point, but it pays with periodic flooding, and state in routers that have no interest. Sparse mode starts empty, and grows. It needs an RP, and it starts with possible detours, but quiet parts of the network never hear about the group at all. IP multicast is still best effort throughout, and neither mode makes it reliable.

[02:48:24] (lec13-multicast.pdf p50) For our laptop, joining a stream is simple. It sends one IGMP report to its local router. Everything else, the joins, the RP, the tree, happens in routers it never hears about. And if it stops listening, those branches get pruned away.

[02:48:45] (lec13-multicast.pdf p50) A group address has no location to route toward. The reverse path check asks about the source, or the tree's root: would I reach it through the port this packet came in on?

[02:48:59] (lec13-multicast.pdf p49) Change the geography. Suppose the RP sits right next to the path. Source to RP costs 2, RP to receiver costs 3, and the direct path costs 5.

[02:49:13] (lec13-multicast.pdf p49) What does a switchover save now? And is the RP then a hot spot, or a bargain?

[02:49:34] (lec13-multicast.pdf p49) Nothing at all. 2 plus 3 equals the direct 5. Switching would add state, for no shorter path. So the shared tree is not inherently bad. The cost of the detour depends on where the RP sits. That finishes our wired story. Packets have reached one host, one of many, and all who asked. But now the laptop unplugs from its wire, and all those assumptions about who can hear whom begin to fall apart.

## Chapter 14: Lecture 14: Wireless

### 14.1 What radio does to bits

[02:50:07] (lec14-wireless.pdf p2) Our laptop leaves the wire. Everything above the link layer still works, in principle. Yet on radio, a frame that was perfect at the sender may be garbage at the receiver, and the sender may have no idea. What actually changes when the wire goes away?

[02:50:27] (lec14-wireless.pdf p2) First, separate two ideas people often mix up. Wireless is about the medium: communicating over a radio link. Mobility is about changing your point of attachment. A fixed sensor is wireless, without being mobile. A laptop moved between wired subnets is mobile, without being wireless. This chapter is about the radio problem. The next is about movement.

[02:50:57] (lec14-wireless.pdf p10) Networks also differ in structure. In infrastructure mode, hosts talk through a base station, such as a Wi-Fi access point or a cell tower, that connects into the wired network. In ad hoc mode, there's no base station, and the nodes organize themselves. And either kind can be single hop or multiple hops, as in a mesh network, where traffic is relayed through other wireless nodes. Two independent questions: is there infrastructure, and how many wireless hops?

[02:51:32] (lec14-wireless.pdf p7) The slides chart radio technologies by rate and range, from Bluetooth at a couple of megabits per second, up through Wi-Fi and cellular generations. Those numbers belong to that era, and aren't promises about today's products. What lasts is the pattern. Higher rates tend to mean shorter range, and every link faces the same questions about frequency, coverage, and sharing. **Clarification:** Rate charts and generation targets are slide-era context, not current deployment facts.

[02:52:00] (lec14-wireless.pdf p11) The channel. Three separate things degrade a radio signal. Path loss: the signal weakens with distance, and when passing through obstacles. Interference: other transmitters and devices add competing energy, since many of them share frequencies like 2 point 4 gigahertz. And multipath: the signal bounces off walls and the ground, so delayed copies arrive at different times, and overlap with each other. An application may see the same symptom from all three, a lost packet, but they aren't the same mechanism.

[02:52:38] (lec14-wireless.pdf p12) To measure signal quality, we compare signal power to noise power. That's the signal to noise ratio, in decibels: 10 times log base 10 of signal over noise. A power ratio of 100 is 20 decibels. Higher SNR means fewer errors. The result is called bit error rate, or BER: the fraction of bits received wrong. These curves show the tradeoff. At the same SNR, a low-rate, robust scheme gives very few errors, while a high-rate scheme fails.

[02:53:15] (lec14-wireless.pdf p36) A radio link can't just pick one rate and stick to it. As a host moves away, SNR falls, and errors climb. Rate adaptation lowers the physical rate, moving to a more robust scheme. Raw rate is not goodput. Repeated failures at a high rate can deliver less than steady success at a low rate. And why not just raise the power? That burns energy, and it interferes with everybody else.

[02:53:46] (lec14-wireless.pdf p12) The rule is, the link's capacity isn't a fixed number. It depends on distance, surroundings, and everyone else who's transmitting at this moment.

[02:53:58] (lec14-wireless.pdf p12) Turning up the power seems like an easy fix for a weak signal. But it drains the battery, and it raises interference for everyone nearby.

[02:54:10] (lec14-wireless.pdf p12) Try the arithmetic. A receiver's signal is 1,000 times stronger than the noise. Then the laptop walks behind a wall, and the ratio drops to 10.

[02:54:23] (lec14-wireless.pdf p12) What are those two values, in decibels? And what should the sender do after the drop?

[02:54:43] (lec14-wireless.pdf p12) 1,000 is 30 decibels. 10 is 10 decibels. That's a large drop, and the sender should adapt to a slower, more robust rate. Each station can react to its own radio conditions. But here's something it can't deal with alone. How do many stations share this one radio channel? Here's a very different answer to that question.

### 14.2 CDMA

[02:55:10] (lec14-wireless.pdf p14) In a crowded room, two pairs can talk at once if one pair speaks English and the other speaks French. You filter out what you can't decode. Could two senders transmit on the same frequency at the same time, with the receiver still separating them?

[02:55:29] (lec14-wireless.pdf p14) That's the idea behind code division multiple access. Each sender gets its own code, a sequence of plus and minus ones, called chips. Sender one uses 1, 1, minus 1, minus 1. Sender two uses 1, minus 1, 1, minus 1. The magic is in how these two relate. Multiply them chip by chip, and add: 1, minus 1, minus 1, plus 1. That's zero. The codes are orthogonal.

[02:56:06] (lec14-wireless.pdf p15) To send a bit, multiply the whole code by the bit's value. Sender one sends plus 1, so it transmits its code unchanged. Sender two sends minus 1, so it transmits its code flipped. On the air, the signals simply add. Chip by chip, the receiver gets 0, 2, minus 2, 0. This sum looks like neither sender.

[02:56:34] (lec14-wireless.pdf p16) Decode. To hear sender one, take the dot product of the received signal with c 1, then divide by 4, the code length. 0 times 1, plus 2 times 1, plus minus 2 times minus 1, plus 0. That's 4, over 4, which is plus 1. Sender one's bit is recovered. With c 2, 0, minus 2, minus 2, plus 0 gives minus 4, over 4, which is minus 1. Why does this work? Correlating with c 1 leaves sender two's contribution multiplied by c 1 dot c 2, and that's zero. Sender two simply vanishes.

[02:57:22] (lec14-wireless.pdf p16) In formula form: the sum of each bit times its code goes out on the air. The receiver takes z dot c k, over M, the code length. This is an ideal model. It assumes synchronized chips and well balanced powers. It's a clean demonstration, not a promise of zero interference in the real world.

[02:57:46] (lec14-wireless.pdf p16) Don't treat orthogonality as magic. It cancels the other sender only under ideal conditions: synchronized chips, balanced powers, and little noise.

[02:57:59] (lec14-wireless.pdf p16) Change one bit. Sender one also sends minus 1, so both bits are minus 1.

[02:58:08] (lec14-wireless.pdf p16) What's the new sum z? And what do you get when you decode each sender?

[02:58:27] (lec14-wireless.pdf p16) z is minus 2, 0, 0, 2. Correlate with c 1: minus 2, plus 0, minus 0, minus 2, which is minus 4, over 4, or minus 1. Correlate with c 2: also minus 4 over 4, or minus 1. Both bits come out right. Codes are one way to share a medium, and cellular networks have used them. But Wi-Fi takes a completely different approach. Before that, a laptop has to find a network to join in the first place.

### 14.3 Joining and moving

[02:59:06] (lec14-wireless.pdf p18) Open your laptop in a coffee shop. Several networks appear, and you click one. What has actually happened? Are you on the Internet yet? And when the frame leaves the laptop, whose address goes on it, the access point's, or the router's?

[02:59:26] (lec14-wireless.pdf p17) Start with the vocabulary. An access point and the stations associated with it form a basic service set, or BSS. Wi-Fi divides its spectrum into channels, and each access point operates on a chosen channel. Neighboring access points on overlapping channels interfere. The SSID is the human-readable network name, and the BSSID identifies one particular BSS. None of these are subnet masks, or IP addresses.

[03:00:00] (lec14-wireless.pdf p20) How do you find one? Two ways. In passive scanning, access points regularly send out beacons, and the laptop just listens. In active scanning, the laptop sends a probe request, and access points answer with probe responses. Either way, you end up with a list of candidates, and you choose one. Passive scanning costs the laptop only listening time. Active scanning finds networks sooner, at the price of a few transmissions.

[03:00:35] (lec14-wireless.pdf p20) That final exchange, a request and a reply, is association. It creates a link-layer relationship with one access point. It doesn't give you an IP address. So your laptop still needs DHCP, then ARP, then DNS, exactly as in chapter 5. Being associated means you can reach the AP, and nothing more.

[03:01:02] (lec14-wireless.pdf p31) The frame. An access point isn't a router. It bridges between radio and Ethernet. So a Wi-Fi frame needs to name both the immediate radio hop, and the final link-layer destination. Say host H1 sends to router R. Address one is the receiver on this radio hop, the AP. Address two is the transmitter, H1. Address three is R's MAC, which is where the AP should bridge the frame. The AP then emits an ordinary Ethernet frame, from H1 to R. H1 stays the Ethernet source. The AP never becomes the IP destination.

[03:01:46] (lec14-wireless.pdf p32) There's also a fourth address field. The slide says address 4 appears only in ad hoc mode, but its own table shows a bridged case. Don't memorize that note as a universal rule. Four-address operation is used for bridging and distribution scenarios. **Clarification:** Four-address operation is a bridging case, not an ad hoc rule (lec14 p32).

[03:02:07] (lec14-wireless.pdf p35) Move. The laptop walks from access point 1 to access point 2. Both connect to one switch, on the same subnet. It associates with AP 2. Its IP address stays valid, because the subnet hasn't changed. So who updates what? The switch does, through its ordinary self-learning. The laptop's next frame arrives on a new port, so the switch's table changes. No Internet routes change. Chapter 2's mechanism handles this mobility case for free.

[03:02:46] (lec14-wireless.pdf p35) Keep the steps apart. Scanning finds an AP, and association attaches to it. Neither one gives you an IP address. That's still DHCP's job, afterward.

[03:03:01] (lec14-wireless.pdf p35) Change the scenario. A new access point has the very same SSID, but it sits behind a different router, on a different IP subnet.

[03:03:13] (lec14-wireless.pdf p35) Does the laptop keep working with its old address? Does matching SSID text guarantee anything?

[03:03:28] (lec14-wireless.pdf p35) It does not keep working. The old address doesn't belong on that subnet, so return traffic gets routed to the wrong place. A matching SSID is just a matching name. What counts is subnet continuity. Crossing subnets is the true mobility problem, and we'll take that on next chapter. First, a problem that hits every Wi-Fi network: when stations share one channel, who's allowed to talk?

### 14.4 Contention and reservations

[03:04:00] (lec14-wireless.pdf p21) Ethernet senders listen before and during transmission, and they abort on a collision. Why can't Wi-Fi do the same thing? It has a radio, it can listen. Is there something about radio that breaks collision detection?

[03:04:18] (lec14-wireless.pdf p22) There are two reasons. First, while transmitting, a radio's own signal overwhelms the tiny signal arriving from elsewhere, so it can't really listen while it talks. Second, and more deeply, what matters isn't what the sender hears. What matters is what the receiver hears. That difference needs a picture.

[03:04:42] (lec14-wireless.pdf p13) A, B, and C sit in a row. Each one's radio range reaches only its neighbors. A hears B. C hears B. But A and C can't hear each other. A senses the channel: silence. It starts sending to B. C senses too: silence, because it's out of A's range. It also starts sending to B. Each sender was perfectly polite, and both frames are destroyed at B. Neither of them noticed anything. This is the hidden terminal problem. Local sensing simply can't see interference at a distant receiver.

[03:05:24] (lec14-wireless.pdf p27) There's a mirror image. Now B sends to A, and C wants to send to D, on the far side. C hears B, so carrier sense says wait. But C's signal wouldn't reach A at all. These two transmissions could have happened at the same time safely. Sensing suppressed useful concurrency. That's the exposed terminal problem. A note of care, though. The slide's shortcut, about hearing an RTS but not a CTS, is an idealized thought experiment. Real timing and acknowledgments must work too, so the drawing alone isn't permission to transmit. **Clarification:** The exposed-terminal shortcut is an idealized argument; real timing rules still apply (lec14 p27).

[03:06:08] (lec14-wireless.pdf p28) Wi-Fi avoids collisions instead of detecting them. It's called CSMA/CA. Here's the sender's routine. Wait until the channel has been idle for a period called DIFS. Then count down a random backoff, one idle slot at a time. If the channel goes busy, freeze the counter. Do not reset it. Transmit when it reaches zero. Then the receiver checks the frame, and after a shorter gap called SIFS, returns an ACK. Why shorter? So the ACK goes first, before anyone else can grab the channel. If no ACK arrives, the sender retries with a larger backoff range.

[03:06:54] (lec14-wireless.pdf p28) Trace a counter. It starts at 4. Two idle slots go by, and it reads 2. Another station transmits for a long time, and the counter stays at 2. When the channel is idle again, two more slots bring it to zero, and we can send. The waiting already done is not thrown away, which makes things fairer for stations that have waited.

[03:07:22] (lec14-wireless.pdf p40) And a missing ACK does not prove a collision. The data might have been corrupted by noise, or the ACK itself might have been lost. Note too that this is a local, link-layer ACK, not TCP's. It repairs one radio hop. Together with coding, retries, and rate changes, that's wireless error recovery. It's done locally because the radio hop is where the errors happen. Local repair doesn't guarantee end to end delivery, though.

[03:07:56] (lec14-wireless.pdf p24) CSMA/CA still doesn't cure the hidden terminal. For that, there's an optional reservation. Before sending data, A sends a short request to send, RTS, to B. B answers with clear to send, CTS. Here's the clever part. CTS comes from the receiver, so everybody near the receiver hears it, including hidden C. Now C knows to stay quiet. Then A sends the data, and B acknowledges.

[03:08:30] (lec14-wireless.pdf p25) How long should C stay quiet? The CTS carries a duration, and C sets a timer, called the network allocation vector, or NAV. This acts as virtual carrier sensing. Even during silent gaps between the protected frames, C treats the channel as busy.

[03:08:52] (lec14-wireless.pdf p26) Is this free? No. RTS frames can themselves collide, but they're short, so a collision costs much less than losing a long data frame. And the four-frame exchange adds overhead. For short frames on a quiet channel, that overhead can exceed what it saves. So choose it for long frames under real contention.

[03:09:17] (lec14-wireless.pdf p37) Radio also costs battery, and listening is expensive. In power management, a station tells its AP it's going to sleep. The AP buffers any frames for it. Each beacon lists who has data waiting. So the station wakes just in time for the beacon, and if it's named, it asks for its frames. Otherwise it goes straight back to sleep.

[03:09:45] (lec14-wireless.pdf p39) Notice the shared pattern with soft state and with queues. The AP holds data on the sleeper's behalf, and a periodic signal tells it when to check. You pay with delay, and you gain battery. There's a tradeoff in every design here.

[03:10:03] (lec14-wireless.pdf p38) Bluetooth shows yet another coordination model. A piconet has one controller, which schedules its nearby devices, so there's no contention at all. It also uses frequency hopping, moving among channels in a pattern. The slide's classic figures are 79 channels, and a 625 microsecond slot. Those describe the classic system, not all Bluetooth modes.

[03:10:33] (lec14-wireless.pdf p38) With 625 microseconds per slot, 1,600 slots fit in one second. The controller grants one client a transmit opportunity at a time, and the group follows a shared hopping sequence. These are classic Bluetooth's numbers, so don't apply them to every mode.

[03:10:55] (lec14-wireless.pdf p38) A hidden terminal isn't simply a weak signal. The key is two senders that can't hear each other, while both reach a shared receiver.

[03:11:06] (lec14-wireless.pdf p26) Test yourself on the geometry. A sends RTS to B. B's CTS is heard by C, which can't hear A. Separately, E can hear A, but not B.

[03:11:20] (lec14-wireless.pdf p26) Which station sets its NAV from the CTS? Which station hears only the RTS? And what might each one do?

[03:11:40] (lec14-wireless.pdf p27) C hears the CTS, so it sets its NAV, and it defers. That protects B's reception. E hears only the RTS. RTS frames also carry a duration, so in the standard behavior, E sets its NAV too, even though it might not harm B. E is exposed, and the shortcut of ignoring it is the idealization we flagged. So the radio link now works, for a laptop that stays put. But what if it doesn't? When a phone drives across a city, changing towers every few minutes, how can a call stay up, and how can anyone even find it?

## Chapter 15: Lecture 15: Cellular and mobility

### 15.1 The cellular core

[03:12:22] (lec15-mobile.pdf p2) Our laptop has become a phone, and now it's moving at highway speed, while it streams video. Its local Wi-Fi tricks are no help at this scale. A cellular carrier must find the phone anywhere in the country, keep its session alive across towers, and bill the right person. What kind of network can do all this?

[03:12:46] (lec15-mobile.pdf p3) Follow the history, since it explains the design. 2G was built for voice, like the telephone network. A radio site, called a BTS, connects to a base station controller, a BSC. Those connect to a mobile switching center, the MSC, and a gateway leads to the public telephone network. It's circuit switched throughout.

[03:13:13] (lec15-mobile.pdf p4) 3G had to add data, without breaking voice. So it built a parallel packet core. The SGSN and GGSN form a data path to the Internet, sitting right beside the unchanged voice path. Voice and data share the radio side, and split at the edge of the core. That's the key insight: coexistence, not replacement.

[03:13:39] (lec15-mobile.pdf p4) Watch one handset use both. Its voice call follows the MSC side. Its packet data follows the SGSN and GGSN side, toward the Internet.

[03:13:54] (lec15-mobile.pdf p5) 4G LTE makes a clean break. Everything, even voice, is carried as IP packets through one all-IP core. There's no separate circuit side. But all-IP doesn't mean ordinary routers and nothing else. LTE keeps specialized machinery for subscribers, authentication, location, radio scheduling, and tunnels.

[03:14:21] (lec15-mobile.pdf p10) Let's assign each piece one main role. The UE, or user element, is the device, along with its subscription. The subscription is identified by an IMSI. This is an identity that stays the same, not a location. The slide calls it 64 bit, and draws it like a MAC address. In the standard, it's a string of no more than 15 decimal digits. The point to keep is that it's separate from any MAC, IP, or tunnel address. **Clarification:** IMSI is a decimal subscriber identity of at most 15 digits, not a MAC address (lec15 p10; 3GPP TS 23.003).

[03:14:56] (lec15-mobile.pdf p11) The eNodeB is the base station. It's not a passive relay. It manages radio resources, and takes an active part in attachment and handover. It's where the wireless hop meets the core.

[03:15:12] (lec15-mobile.pdf p11) For example, base station A decides that a target, B, should serve a moving phone. It asks B for resources, and later directs the phone there. The core's tunnel state then moves to match. An ordinary Ethernet switch does nothing like this.

[03:15:32] (lec15-mobile.pdf p12) The home subscriber server, the HSS, lives in the subscriber's home network. It stores who you are and what you're allowed to do, and it cooperates in authentication. It isn't on the path of your data at all.

[03:15:49] (lec15-mobile.pdf p12) Picture a phone appearing in a visited network. Its mobility manager coordinates with the home HSS, to authenticate the subscription and set up state for the visit. That's a database and control role. No user packet ever passes through it.

[03:16:08] (lec15-mobile.pdf p14) The mobility management entity, the MME, is the coordinator. It handles authentication with the HSS, tracks where the device is, handles paging, and sets up the tunnels. It tells other boxes what to do, but user data doesn't pass through it.

[03:16:28] (lec15-mobile.pdf p13) The serving gateway and the packet gateway are on the user's data path. The P-GW connects to external networks, such as the Internet. The S-GW joins the radio-side tunnel to the tunnel toward the P-GW. To see the point, watch a packet. It goes UE, eNodeB, S-GW, P-GW. It never touches the MME or the HSS.

[03:16:58] (lec15-mobile.pdf p13) The P-GW is the cellular system's outward doorway. The radio cell can change, while traffic stays anchored through that gateway. It may also perform NAT. But NAT translation and tunnel encapsulation are different operations, so don't treat them as one.

[03:17:18] (lec15-mobile.pdf p15) Draw two separate pictures. The control story has the HSS and the MME. The payload story has the S-GW and the P-GW. A control message can change a data path without its sender being one of the hops. That's the data plane and control plane split again, from chapter 3.

[03:17:41] (lec15-mobile.pdf p15) A tempting error is to route user data through every box in the diagram. The HSS and MME do control work. Payload travels through the base station, the S-GW, and the P-GW.

[03:17:57] (lec15-mobile.pdf p14) Test that. Suppose the MME crashes for a moment, while a phone is sitting still, in the middle of a video stream. Separately, suppose the S-GW crashes.

[03:18:12] (lec15-mobile.pdf p14) Which failure immediately stops the video's packets? And which one affects moving phones, and new ones?

[03:18:28] (lec15-mobile.pdf p13) An S-GW failure stops the packets right away, since it's on the data path. The tunnels that are already set up don't pass through the MME, so its failure hits control tasks first, like attaching, paging, and handover. So, the data flows through a chain of tunnels. What's inside those tunnels, and how does the radio hop actually work? That's next.

### 15.2 Radio stack and tunnels

[03:18:56] (lec15-mobile.pdf p16) A phone's IP packet has to cross a noisy radio link, then a carrier's core network, and every few minutes the radio end of that path moves. How do you carry a packet through all that, so the packet itself never needs to know?

[03:19:14] (lec15-mobile.pdf p16) Start with the radio hop. LTE splits its link layer into pieces. PDCP handles header compression and encryption, so scarce radio bits aren't wasted on bulky headers. RLC handles fragmentation and reassembly, and reliable transfer over the radio. Below that sits the medium access layer. Note that RLC segmentation is not IPv4 fragmentation. The headers are different, and so is the scope of reassembly. The radio link fixes its own problems locally.

[03:19:52] (lec15-mobile.pdf p17) How do users share the radio? Unlike Wi-Fi, there's no contention for the downlink. The base station is a scheduler. It uses OFDM, which divides the channel into many orthogonal frequency subcarriers. Picture a grid, with time along one axis, and frequency along the other. The scheduler hands each small block to one user. A user with good conditions may get more. That grid only shows opportunities, and doesn't give you application throughput, because coding, modulation, and overhead still apply.

[03:20:33] (lec15-mobile.pdf p18) The core. Inside the core, the phone's packet isn't routed by its own address. It travels in a tunnel, using GTP, the GPRS tunneling protocol. The eNodeB wraps the phone's IP packet in a GTP header, that in UDP, and that in an outer IP header addressed to the S-GW. Core routers read only that outer header. The S-GW then unwraps and rewraps, into a new tunnel toward the P-GW. There the outer layers come off, and the original packet heads into the Internet, unchanged.

[03:21:12] (lec15-mobile.pdf p18) What's the benefit of all that wrapping? The radio end of the tunnel can change, without every Internet router learning a new route for this phone. The inner address stays fixed, while only the outer destination moves. And the core needs nothing beyond plain IP routing.

[03:21:32] (lec15-mobile.pdf p19) How does a phone get started? It first synchronizes with a nearby cell, and reads broadcast system information. It selects a base station. Then control setup, with authentication through the MME and HSS. And finally the data path is built. Finding a signal doesn't prove that a tunnel, or even an authorized subscription, is ready. Those are distinct stages.

[03:22:02] (lec15-mobile.pdf p20) Radios drain batteries, so an idle phone sleeps. It can go into a deeper sleep, where it no longer tracks a specific cell, and then the network knows it only roughly. To reach it, the network pages it across that area. When it wakes, it might have moved, and may need a new association. It's the same trade-off as Wi-Fi sleep: battery against delivery, with cellular machinery.

[03:22:32] (lec15-mobile.pdf p20) Follow one phone. It sleeps, moves into another cell, and then becomes active. The old radio path can't simply be assumed, so it may need to reestablish access through the new cell before traffic can resume.

[03:22:49] (lec15-mobile.pdf p22) One more view. Carriers are networks of IP networks, joined by interconnections, just like the rest of the Internet. Your phone might attach in a visited network, while your subscriber record stays at home, in your home carrier's HSS. So every topic in this course reappears here: tunnels, routers, and policy agreements between providers.

[03:23:16] (lec15-mobile.pdf p23) 5G New Radio extends the physical layer. Higher frequencies offer more capacity, but shorter range, so cells must be much denser. MIMO uses many antennas to send and receive multiple spatial streams. The slide's specific rates and goals describe the era of those slides, so treat them as context. The trade-off is what lasts: more spectrum and antennas for capacity, paid for with deployment density.

[03:23:48] (lec15-mobile.pdf p23) Don't mix these up. CDMA separates senders by code. OFDM organizes the channel by frequency and time, and the scheduler hands out those resources.

[03:24:02] (lec15-mobile.pdf p18) Look at one packet, deep in the core, between S-GW and P-GW. Its inner destination is a web server on the Internet.

[03:24:14] (lec15-mobile.pdf p18) Which address does a core router in the middle use to forward it? Does that router need a route to the phone?

[03:24:29] (lec15-mobile.pdf p18) It reads the outer destination, the P-GW. It needs no route to the phone at all. That's the whole benefit: a carrier's core routers know nothing about individual subscribers. And now the big question. Your phone has moved between cities, or even to another carrier's network. Its identity hasn't changed, but where it sits has. How does anybody find it?

### 15.3 Finding a moving phone

[03:24:58] (lec15-mobile.pdf p25) The problem that was planted back in chapter 3. An IP address says where you are in the topology. That's what makes routing scale. So what happens when you move? Your old address now points to the wrong place. But your identity, the thing others use to contact you, hasn't changed. One number has been doing two jobs.

[03:25:25] (lec15-mobile.pdf p26) One approach: let the routing system handle it. Have the phone advertise its own slash 32 from wherever it is. Routers would find it, in principle. But think about billions of devices, each changing location constantly, with each change spreading through every router in the world. That would be enormous, rapidly changing routing state. And it would destroy the very aggregation that makes routing scale. So we push the problem to the edge instead.

[03:25:59] (lec15-mobile.pdf p29) Split the two roles. The home network is the provider you subscribe to. It always knows who you are. The visited network is wherever you currently are. It provides access, and tells your home where you've gone. This happens even between countries. In cellular, the HSS is on the home side. The generic Mobile IP example and LTE share this principle, even though the protocols and components have different names.

[03:26:33] (lec15-mobile.pdf p31) A constructed Mobile IP example. The mobile's home address is 192.0.2.20. On arriving at a visited network, it gets a current locator, called a care-of address, 198.51.100.44. It registers this with its home agent, which records a binding from home address to care-of address. The drawing has a foreign agent ending the tunnel. A co-located care-of address, where the mobile itself ends the tunnel, is another valid arrangement. And don't mix this generic Mobile IP up with LTE's HSS, MME, and GTP. **Clarification:** The foreign-agent drawing is one Mobile IPv4 arrangement; do not conflate it with LTE (lec15 p34; RFC 5944).

[03:27:18] (lec15-mobile.pdf p34) A correspondent sends to the mobile. It uses the home address, not knowing anything has changed. The packet arrives at the home network. The home agent intercepts it, and puts the whole packet inside a new one: an outer IP header, from the home agent to the care-of address. That's IP tunneling. Routers in the middle follow only the outer header. At the far end, the outer header comes off, and out comes the original packet, with its source and destination unchanged. This is indirect routing. The correspondent never needed to know about the move.

[03:28:00] (lec15-mobile.pdf p34) Tunnels cost bytes. An illustrative outer IPv4 header adds 20 bytes. A 1,480 byte inner packet becomes 1,500, which just fits an Ethernet link. A 1,500 byte inner packet becomes 1,520, and that needs different MTU treatment. And don't confuse tunneling with NAT. NAT rewrites addresses. A tunnel adds an envelope.

[03:28:32] (lec15-mobile.pdf p34) Watch the mobile move again, to a new locator, 203.0.113.44. It re-registers. The home agent updates its binding. The outer destination changes. The inner destination stays right where it was. That's the visual to hold on to: identity in blue, unchanged, and location in the outer header, changing.

[03:29:02] (lec15-mobile.pdf p35) What's the downside of indirect delivery? A detour. Traffic goes through the home agent, even when the correspondent is right next to the mobile. This is triangle routing. In this constructed example, the correspondent to home agent takes 40 milliseconds. Then 50 more to the mobile. That's 90, while a direct path would only take 10. It's a detour, not a loop.

[03:29:32] (lec15-mobile.pdf p36) Direct routing removes the detour. The correspondent obtains the current locator, then tunnels straight to it. It saves 80 milliseconds here. But the price is complexity. The correspondent must now handle bindings. And when the mobile moves again, something must handle packets aimed at the old location. Neither design removes location state. It only changes who holds and uses it.

[03:30:04] (lec15-mobile.pdf p36) When you trace a tunnel, always say which header you mean. The outer destination changes. The inner source and destination don't. An answer that just says, the destination, is ambiguous.

[03:30:20] (lec15-mobile.pdf p35) Change the geography. Correspondent to home agent is 60 milliseconds. Home agent to mobile is 70. Direct is 5.

[03:30:33] (lec15-mobile.pdf p35) What's the one-way delay with each design? And if the correspondent is actually beside the home agent, does the triangle still hurt?

[03:30:56] (lec15-mobile.pdf p35) Indirect is 130 milliseconds, and direct is 5. But if the home agent is near the path anyway, the detour shrinks to nothing. It depends on geometry. Now one piece remains. All of this assumed a phone that has already arrived somewhere. What about the moment of moving itself, in the middle of a video, from one tower to another?

### 15.4 Handover

[03:31:23] (lec15-mobile.pdf p38) A phone at highway speed leaves one cell, and enters the next, in the middle of a stream. The radio link must move. The tunnel must move. Packets are already in flight toward the old tower. How can you change all of this without dropping the session?

[03:31:43] (lec15-mobile.pdf p39) This is handover. Here's the setup. Packets come from the S-GW through a tunnel to base station A, then over the radio to the phone. Base station B sits next door, and it's stronger as the phone drives toward it. Base station A notices this from the phone's radio reports.

[03:32:06] (lec15-mobile.pdf p40) Step one. A chooses B as the target, and asks it to get ready. Step two. B reserves radio resources, and acknowledges. Nothing has moved yet, and the phone keeps working as before. Prepare first, and then act, so that the target is ready when the phone arrives.

[03:32:29] (lec15-mobile.pdf p40) Step three. A tells the phone to switch, and the phone begins using B. The radio has moved. But the S-GW has not been told, and it's still sending to A. So what happens to those packets? Step four. A forwards them to B, over a temporary path. So during this period, the path is S-GW, A, B, phone. It's longer, but nothing's lost.

[03:33:01] (lec15-mobile.pdf p40) Step five. B reports that the move is complete. The MME tells the S-GW to change its tunnel endpoint from A to B. See that this is a control message, and the MME isn't carrying any data. Step six. The S-GW now sends straight to B, and A releases its old resources. The outer destination changed. The inner packet, and the phone's IP address, did not.

[03:33:33] (lec15-mobile.pdf p40) There are three paths to remember. Before: S-GW, A, phone. During: S-GW, A, B, phone. After: S-GW, B, phone. The middle stage explains how the radio can finish moving before the core catches up.

[03:33:54] (lec15-mobile.pdf p41) Does a preserved IP address mean nothing changes for TCP? No. The longer forwarding path raises delay for a while. Packets can arrive out of order. Radio errors and local retries make round trip times swing around. IP is still best effort, and its contract hasn't changed. But TCP might read these effects as congestion, even when no queue is full. The details of transport belong to later lectures. For now, keep the link: what lower layers do can change the performance higher layers see.

[03:34:35] (lec15-mobile.pdf p41) During handover, notice who carries what. The MME only sends control messages. The data goes from the S-GW, through A, and on to B.

[03:34:48] (lec15-mobile.pdf p40) Change the order. Imagine a design where the S-GW switches its tunnel to B first, before the phone has actually moved.

[03:34:59] (lec15-mobile.pdf p40) What happens to packets for those moments? And is there any forwarding path that would save them?

[03:35:14] (lec15-mobile.pdf p40) Packets reach B, but the phone is still attached to A, so B has nobody to give them to. They would need buffering, or they'd be lost. The real ordering avoids this: the radio moves first, and packets follow, by way of A, and only then does the core switch. Order matters, just as it did with routing convergence. And with that, every piece of the story is in place. So let's put it all together, one last time.

## Chapter 16: Synthesis

### 16.1 The whole story, then mixed problems

[03:35:46] (lec10-routing.pdf p3) We began with one question. How does a packet reach the right place, when no device knows the whole path? Now we can answer it. Every mechanism in this course supplies one missing fact, keeps some state, picks one action, or contains one failure. Let's retell the entire journey, and then test it on problems that cross chapters.

[03:36:13] (lec09-discovery.pdf p9) A laptop wakes up. Wi-Fi association attaches it to an access point, and a broadcast to DHCP gives it an address, mask, gateway, and resolver. Its mask says the resolver is remote, so ARP finds the gateway's MAC address. A frame carries the DNS query to R1. The resolver walks the hierarchy, using caches when it can, and returns an A record. Now the laptop can send to the server.

[03:36:46] (lec06-lan.pdf p30) The frame crosses switches, which learned their tables from source addresses. At R1 the frame is replaced, while the packet's endpoints stay fixed, and TTL drops by one. Longest prefix match selects the output. The packet crosses the fabric, waits in a queue, and leaves. Those tables came from the control plane: link state or distance vector inside an AS, and BGP between ASes, shaped by contracts, with the next hop resolved through internal routing.

[03:37:24] (lec11-convergence.pdf p10) When something breaks, detection, propagation, computation, and installation all take time, and in between come blackholes and loops. If the destination is a group, IGMP learns local interest, and PIM connects the routers. If it's one of many, routing picks an instance. And when the receiver moves, a tunnel carries the same inner packet to a changing outer destination, while control messages move the endpoints. The envelope is local, and the packet is global. At each layer, the question is who knows what.

[03:38:03] (lec10-routing.pdf p15) Before the problems, one last trap. Exam answers go wrong when mechanisms blur together. Each one supplies one missing fact. Name the fact first, and then the mechanism.

[03:38:19] (lec08-network2.pdf p5) Mixed problems. Problem one. A host at 10.10.1.97/23 sends to 10.10.0.200. Then to 10.10.2.5. Its gateway is 10.10.0.1. Which IP address does it ARP for, each time? Think in terms of the mask.

[03:38:46] (lec08-network2.pdf p5) The block covers third byte values 0 and 1. So 10.10.0.200 is local, and the host ARPs for 10.10.0.200 itself. 10.10.2.5 is outside the block, so it ARPs for its gateway, 10.10.0.1. The mask decides, not how the numbers look.

[03:39:17] (lec11-convergence.pdf p16) Problem two. A router uses distance vector. Its link to neighbor A costs 2, and A says 7. Its link to neighbor B costs 5, and B says 1. Which route wins? Then the destination fails, and B had been routing through this very router. What goes wrong, and which fix applies?

[03:39:42] (lec11-convergence.pdf p16) Through A costs 9, and through B costs 6, so B wins. But wait. If B reaches the destination through this router, then B's advertised 1 could be stale, with no real path behind it. The result is count to infinity, on a two-node dependency. Poison reverse would have had B advertise infinity back to us, so that the false route would never have been considered at all.

[03:40:17] (lec12-bgp.pdf p14) Problem three. Your AS has a route from a provider with local preference 80 and an AS path of length 2, and a route from a customer with local preference 100 and length 5. You pick one. Which do you use? And would you advertise the other to your peer?

[03:40:38] (lec12-bgp.pdf p14) You use the customer route, because preference comes first, so path length never comes into it here. You'd advertise that customer route to your peer, since customer routes go everywhere. The provider route you would not offer to a peer, even if it were your only route, because that would make you carry traffic between two non-customers.

[03:41:07] (lec07-network1.pdf p37) Problem four. A 2,000 byte datagram, with a 20 byte header, must cross a link with an MTU of 1,500. Which bytes go in the first fragment? What offset does the second one carry? Then its destination, 201.10.6.200, meets the same three-entry table as before. Which output?

[03:41:34] (lec07-network1.pdf p37) The data is 1,980 bytes. The first fragment carries 1,480, at offset 0, with the more fragments flag set. The second carries 500, at offset 185, with the flag cleared. For lookup, 201.10.6.200 matches the slash 21, the slash 23, and the slash 0, so the slash 23 wins: output B. Each fragment gets the same lookup, since every fragment has the same destination.

[03:42:17] (lec13-multicast.pdf p32) Problem five. A multicast router reaches source S through port 2. A packet from S to group G arrives on port 4, and later on port 2. Its LAN has one member, and that member sends a leave. What happens at each step?

[03:42:37] (lec13-multicast.pdf p32) On port 4, the reverse path test fails, so it's dropped as a likely duplicate. On port 2, it passes, and the packet is forwarded onto interested outputs. When the member leaves, the router doesn't prune right away. It sends a group-specific query, since others might remain. When no one answers, it stops forwarding there, and if no other branches want the data, it prunes upstream. IGMP handled the LAN, and PIM handled the routers.

[03:43:17] (lec15-mobile.pdf p7) Last one. A phone's tunnel runs through S-GW to base station A, and a correspondent reaches the phone's stable address. The phone hands over to base station B. Which fields change in the packet that the S-GW sends afterward?

[03:43:36] (lec15-mobile.pdf p7) Name exactly what changes, and what stays the same.

[03:43:48] (lec15-mobile.pdf p7) The outer destination changes, from A to B. The inner packet stays the same. That's the picture you started this course with, one final time. The blue address persists, while an outer envelope changes around it. At the very beginning it was yellow, on one Ethernet link. Now it's a tunnel across a cellular core. It's the same idea at a new scale. When you face a new mechanism, ask what's missing, who knows it, what state is kept, and what happens when that state goes stale. If you can trace one packet through it with real addresses, you understand it. Next, try the practice midterm walkthrough in chapter 13, and use the study player to answer before each explanation.
