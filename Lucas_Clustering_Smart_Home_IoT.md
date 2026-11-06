# Lucas Sequence-Guided Clustering and Graph Optimization for Survivable Smart Home IoT Networks

**Kanaka Raju Rajana, Shanmuk Srinivas Amiripalli**  
*Department of Computer Science and Engineering, GST, GITAM Deemed to be University, Visakhapatnam, Andhra Pradesh, India*  
*E-mail: krajana@gitam.edu, shamnuk39@gmail.com*

---

### Abstract
Residential Internet of Things (IoT) deployments require underlying networks that maintain end-to-end data delivery even as individual sensing nodes fail from battery exhaustion or hardware faults. This study investigates a deterministic clustering framework derived from consecutive terms of the Lucas sequence, integrated with Trimetric Graph Optimization (TGO) and the Routing Protocol for Low-Power and Lossy Networks (RPL) over UDP. A 72-node network is partitioned into six progressively sized clusters containing 3, 4, 7, 11, 18, and 29 nodes. Each cluster routes member traffic through a designated cluster head connected directly to an RPL destination-oriented directed acyclic graph (DODAG) root, while TGO prunes redundant intra-cluster communication edges while preserving path redundancy. Over a 12-round simulated fault injection benchmark in Contiki-NG/COOJA, the Lucas-TGO architecture was evaluated against an equal-sized TGO topology, a cluster-tree arrangement, and an unpruned mesh. By round 12, all three benchmark topologies experienced complete network failure (0 active nodes). In contrast, the Lucas-TGO network maintained approximately 54 active nodes (75% retention), kept its packet delivery ratio above 90%, bounded end-to-end delivery latency between 19 ms and 25 ms, and consumed approximately 1.5 J per node (compared to 12.2 J per node in the equal-cluster TGO baseline). These results demonstrate that combining graded cluster sizing with algorithmic link reduction improves fault tolerance and delays catastrophic partitioning in resource-constrained IoT systems.

**Keywords:** Internet of Things, smart home networks, Lucas sequence, clustering optimization, network survivability, fault tolerance, RPL.

---

## 1. Introduction

Modern smart residential environments incorporate dense networks of small, battery-operated embedded sensors and actuators. These devices govern heating, ventilation, automated lighting, security systems, sub-metering, and home healthcare infrastructure. Because residential automation systems operate continuously with minimal manual maintenance, the wireless mesh must tolerate regular node dropouts without experiencing complete communication blackouts. Physical enclosures, concrete partition walls, 2.4 GHz spectrum interference, and battery depletion frequently disable transceivers. When critical forwarding nodes fail, the network risks fragmenting into disconnected segments, halting telemetry and automated control loops.

Clustering represents a well-established strategy for managing transmission overhead in such environments. By grouping devices under a representative cluster head (CH), local member nodes transmit over shorter distances, while the cluster head aggregates and forwards telemetry toward the gateway. Extensive surveys document the role of clustering in mitigating radio energy expenditure and extending operational spans in wireless sensor networks (WSNs) [1], [2]. Recent efforts have largely focused on adaptive heuristics, metaheuristic algorithms, and machine learning methods to improve cluster-head selection and inter-cluster routing [3]–[6].

Most existing formulations optimize for network lifetime or aggregate power consumption under standard operational conditions. Network survivability—the capacity to maintain operational data delivery paths while experiencing progressive, non-uniform node loss—is often treated as a secondary byproduct rather than an explicit design objective. Although targeted survivability frameworks exist [7]–[11], they rarely explore how structural variance in cluster dimensions affects resilience against cascading dropouts.

Standard clustering schemes conventionally enforce uniform cluster sizes or form clusters dynamically through iterative runtime negotiation. This work explores a different approach: sizing clusters deterministically using mathematical sequences. The Lucas sequence ($2, 1, 3, 4, 7, 11, 18, 29, \dots$) satisfies the same recurrence relation as the Fibonacci series ($L_n = L_{n-1} + L_{n-2}$) but begins from initial values $L_0 = 2$ and $L_1 = 1$ [12]. Using successive Lucas terms produces an asymmetric, graded distribution of cluster sizes whose convergence toward the golden ratio ($\phi \approx 1.618$) balances forwarding overhead and node concentrations across the topology.

This paper evaluates a Lucas-guided clustering design for smart home IoT installations. A 72-node wireless sensor topology is divided into six clusters corresponding to consecutive Lucas numbers ($L_2$ through $L_7$). Cluster heads interface directly with an RPL sink acting as the root of a destination-oriented directed acyclic graph (DODAG) [13], handling sensor readings transmitted via UDP. Intra-cluster topologies are refined using Trimetric Graph Optimization (TGO) to eliminate redundant links while preserving detour paths.

The primary contributions of this paper are:
1. **Sequence-Guided Cluster Partitioning:** A closed-form deterministic cluster sizing formulation based on Lucas numbers that maps directly to total node count identities.
2. **Layered Routing Architecture:** Combining TGO link pruning inside individual clusters with RPL DODAG uplinks from each cluster head to the sink node.
3. **Survivability Evaluation:** A comparative simulation benchmark assessing node retention, cumulative energy expenditure, packet delivery ratio (PDR), and transit latency across 12 fault-injection rounds.
4. **Isolated Comparative Baselines:** Decoupling the performance impact of link pruning from cluster sizing by benchmarking against equal-cluster TGO, unpruned mesh, and cluster-tree configurations.

The remaining sections are structured as follows: Section 2 reviews related literature. Section 3 details the system model, Lucas formulation, TGO algorithm, and baseline configurations. Section 4 presents the experimental environment, empirical curves, and comparative analysis. Section 5 summarizes findings and suggests practical extensions.

---

## 2. Related Work

### 2.1 Energy-Efficient Clustering in WSN and IoT Environments
Clustering taxonomies categorize protocols by their clustering criteria, rotation mechanisms, and adaptation to network heterogeneity [1], [2]. Recent contributions explore varied optimization paradigms: Goel et al. [3] implemented adaptive hybrid optimization for cluster formation; Zhang et al. [6] applied artificial bee colony searches to multi-hop cluster layouts; Lonkar et al. [5] examined empirical hybrid algorithms for cluster-head selection; and Hu et al. [4] utilized feature-graph neural networks (FGOGNN) for routing decisions.

A persistent challenge in clustered data gathering is the energy hole or hotspot problem, where nodes in closer proximity to the base station exhaust their batteries prematurely due to heavy relaying duties [14]. In medical telemetry settings, Manchanda et al. [15] applied fuzzy logic alongside metaheuristics to balance cluster configurations, while Koyalil and Rajalingam [16] surveyed bio-inspired algorithms targeting operational longevity. While learning and search-based heuristics offer dynamic adaptability, they introduce computational and signalling overhead during setup and re-clustering phases.

### 2.2 Fault Tolerance and Network Survivability
Survivability analysis examines whether a communication topology remains functional during progressive physical attrition. Mansour et al. [10] developed an energy-aware fault-tolerant clustering protocol explicitly targeting sensor survivability. Yang et al. [17] introduced dynamic hierarchical backup heads to maintain connectivity in underwater acoustic-optical sensor networks. Structural resilience has also been studied through virtualization layers [7], dynamically relocated sink topologies [8], and mobile data collectors in unattended environments [18].

Moving toward testbed validation, Elappila and Chinara [9] implemented survivability protocols on Contiki-OS across physical hardware motes. Complementary investigations cover distributed self-healing algorithms [19], edge application state recovery [20], trust-based virtual network embedding [21], node importance evaluations under heavy network load [22], operational compliance verification in power distribution grids [23], and system decay under targeted resource exhaustion attacks [11].

### 2.3 Broader Uses of Clustering in IoT Systems
Clustering also serves diverse functions beyond radio topology management. Examples include process mining trace classification in industrial workflows [24], congestion-managed data queues in medical cloud networks [25], and requirement grouping during IoT software engineering cycles [26].

### 2.4 Research Gap
Table 1 outlines key representative studies. Prior research relies almost exclusively on dynamic discovery, stochastic metaheuristics, or iterative cluster formation. The use of deterministic integer sequences to partition network sizing remains unexamined. This paper investigates whether an asymmetric, sequence-driven cluster hierarchy combined with graph pruning provides measurable survivability advantages over traditional uniform-clustering strategies.

#### Table 1: Summary of Representative Studies
| Reference | Primary Focus | Methodology | Relevance to Present Study |
| :--- | :--- | :--- | :--- |
| **[1]** | Energy efficiency in WSN clustering | Survey / Taxonomy | Foundational principles of cluster energy dissipation |
| **[2]** | Heterogeneous dynamic clustering | Systematic literature review | Motivates the use of non-uniform cluster sizing |
| **[3]** | Energy-efficient WSN clustering | Adaptive hybrid optimization | Algorithmic baseline; contrasts with deterministic partitioning |
| **[6]** | Multi-hop cluster topologies | Artificial bee colony metaheuristic | Explores multi-hop intra-cluster overheads |
| **[4]** | Graph-driven cluster routing | Graph neural network (FGOGNN) | Graph-theoretic representation of sensor networks |
| **[10]** | Fault-tolerant sensor clustering | Energy-aware protocol engineering | Core objective: sustaining packet flow during node loss |
| **[17]** | Survivable underwater sensor networks | Dynamic hierarchical backup heads | Demonstrates the utility of secondary cluster heads |
| **[9]** | IoT protocol implementation | Contiki-OS on hardware testbed | Practical blueprint for embedded verification |
| **[15]** | Clustered healthcare monitoring | Fuzzy logic and metaheuristics | Multi-constraint optimization in constrained topologies |

---

## 3. Proposed Methodology

### 3.1 Network Model
The smart home deployment is modeled as an undirected graph $G = (V, E)$, where the vertex set $V$ ($|V| = N = 72$) represents stationary sensor motes deployed across interior residential spaces, and $E$ represents bidirectional wireless communication links. A single sink node acts as the data collection gateway. Nodes remain stationary post-deployment. Over successive operational rounds $r \in \{1, 2, \dots, 12\}$, individual nodes exhaust their batteries or fail randomly. The remaining active subgraph $G'(r) = (V'(r), E'(r))$ determines whether telemetry packets successfully reach the sink.

### 3.2 Lucas Sequence-Based Cluster Sizing
The classical Lucas integer recurrence is given by:
$$L_0 = 2, \quad L_1 = 1, \quad L_n = L_{n-1} + L_{n-2} \quad \text{for } n \ge 2$$
generating the series $2, 1, 3, 4, 7, 11, 18, 29, 47, 76, \dots$

The proposed scheme defines six distinct cluster groups whose member quotas correspond to six consecutive Lucas terms starting at index $k = 2$:
$$S_k = L_{k+1}, \quad k \in \{1, 2, \dots, 6\}$$
yielding cluster capacities:
$$(S_1, S_2, S_3, S_4, S_5, S_6) = (3, 4, 7, 11, 18, 29)$$

The total network capacity matches the established Lucas summation identity $\sum_{i=0}^m L_i = L_{m+2} - 1$:
$$N = \sum_{k=1}^6 S_k = \sum_{i=2}^7 L_i = (L_9 - 1) - (L_0 + L_1) = (76 - 1) - (2 + 1) = 72$$

Because consecutive Lucas terms satisfy $\lim_{n \to \infty} \frac{L_{n+1}}{L_n} = \phi \approx 1.618$, each successive cluster accommodates roughly 1.6 times more nodes than the preceding one. This distribution avoids assigning identical traffic loads across all cluster heads, allowing the network to retain functional pathways across differently scaled clusters as nodes drop out.

### 3.3 Cluster Heads, Routing Structure, and Transport
Each cluster elects a single cluster head ($CH_k$) responsible for gathering readings from member nodes across intra-cluster paths and relaying aggregated packets to the sink:
* **Cluster 1 ($S_1 = 3$ nodes):** Node 1 ($CH$)
* **Cluster 2 ($S_2 = 4$ nodes):** Node 4 ($CH$)
* **Cluster 3 ($S_3 = 7$ nodes):** Node 8 ($CH$)
* **Cluster 4 ($S_4 = 11$ nodes):** Node 15 ($CH$)
* **Cluster 5 ($S_5 = 18$ nodes):** Node 26 ($CH$)
* **Cluster 6 ($S_6 = 29$ nodes):** Node 44 ($CH$)

The sink acts as the DODAG root under RPL [13]. Cluster heads establish dedicated upward RPL routing entries toward the root, separating intra-cluster local data collection from primary inter-cluster transit. Sensor packets travel via UDP.

### 3.4 Trimetric Graph Optimization (TGO)
Dense intra-cluster connectivity increases transmission collisions, idle listening, and routing control overhead. TGO prunes dense intra-cluster cliques down to a reduced edge set $E'_k \subset E_k$. The optimization retains direct star links between the cluster head and member nodes while maintaining a sparse set of peripheral lateral edges among neighboring motes. These lateral edges provide alternate local detours if a direct link to the cluster head degrades, preventing member isolation without maintaining a complete mesh.

### 3.5 Execution Workflow
1. Calculate cluster capacities $S_k$ using the Lucas recurrence ($S_1=3$ to $S_6=29$) and confirm $\sum S_k = 72$.
2. Assign sensor devices to the six clusters based on these quotas.
3. Designate the cluster head node for each group.
4. Establish candidate local wireless links between motes within transmission range.
5. Apply TGO pruning to reduce intra-cluster edge density while maintaining redundant detour paths.
6. Connect all six cluster heads to the RPL sink to construct the DODAG.
7. Execute the 12-round simulation under fault injection, recording active node counts, energy depletion, PDR, and end-to-end latency.

### 3.6 Benchmark Topologies
To isolate whether performance changes stem from link pruning or cluster sizing, the proposed system was evaluated against three control configurations (Table 2):
* **Equal TGO:** The 72 nodes are divided into six uniform clusters of 12 nodes each, with intra-cluster links pruned via TGO.
* **Mesh Network:** Six uniform clusters of 12 nodes each, maintaining full unpruned intra-cluster cross-links.
* **Cluster Tree:** Eight symmetrical clusters of 9 nodes each (1 cluster head + 8 member nodes in a strict star arrangement) connected to the sink root.

Comparing Mesh against Equal TGO isolates the benefit of link pruning. Comparing Equal TGO against Lucas TGO isolates the benefit of sequence-guided sizing.

#### Table 2: Evaluated Network Topologies
| Topology | Cluster Configuration | Intra-Cluster Structure | Cluster Head to Sink Uplink |
| :--- | :--- | :--- | :--- |
| **Lucas TGO (Proposed)** | 6 clusters: 3, 4, 7, 11, 18, 29 nodes | Pruned via TGO | Direct RPL-UDP uplink |
| **Equal TGO** | 6 uniform clusters: 12 nodes each | Pruned via TGO | Direct RPL-UDP uplink |
| **Cluster Tree** | 8 uniform clusters: 9 nodes each ($1 CH + 8$ leaves) | Strict star (leaves to CH only) | Direct RPL-UDP uplink |
| **Mesh Network** | 6 uniform clusters: 12 nodes each | Unpruned full mesh | Direct RPL-UDP uplink |

---

## 4. Performance Evaluation and Analysis

### 4.1 Simulation Environment
Simulations were conducted in Contiki-NG utilizing the COOJA network simulator. The virtual motes emulate CC2420 IEEE 802.15.4 transceivers deployed over a 200 m $\times$ 200 m residential propagation area using the Unit Disk Graph Model (UDGM) with distance loss. Table 3 specifies the runtime parameters.

#### Table 3: Simulation Parameters
| Parameter | Configuration Setting |
| :--- | :--- |
| **Network Scale** | 72 sensor motes + 1 sink gateway (RPL Root) |
| **Network Topologies** | Lucas TGO, Equal TGO, Cluster Tree, Mesh |
| **Protocol Stack** | RPL (Non-Storing/Storing DODAG) over UDP / IPv6 |
| **Evaluation Span** | 12 discrete operational rounds |
| **Simulator Platform** | Contiki-NG / COOJA simulation tool |
| **Propagation Model** | UDGM Distance Loss; $R_{tx} = 50\text{ m}$, $R_{int} = 60\text{ m}$ |
| **Initial Energy Reserve** | 20.0 Joules per node |
| **Traffic Characteristics** | Constant Bit Rate (CBR): 1 packet per 60 s per node; 30-byte payload (40 bytes total at network layer) |
| **Fault Injection Model** | Combined energy depletion and 5% random node failure per round |
| **Statistical Replication** | 10 independent seeded runs; results plotted as ensemble averages |

### 4.2 Evaluation Metrics
For each round $r \in \{1, 2, \dots, 12\}$:
1. **Network Survivability ($SR$):** The proportion of surviving active nodes $A(r)$ relative to initial count $N$:
   $$SR(r) = \frac{A(r)}{N} \times 100\%$$
2. **Mean Energy Dissipation per Node ($E_{\text{avg}}$):** Cumulative energy consumed across the network divided by initial node count:
   $$E_{\text{avg}}(r) = \frac{1}{N} \sum_{i=1}^N E_i(r) \quad \text{[Joules]}$$
3. **Packet Delivery Ratio ($PDR$):** The ratio of successfully received packets at the sink $P_{rx}(r)$ to total packets generated by active nodes $P_{tx}(r)$:
   $$PDR(r) = \frac{P_{rx}(r)}{P_{tx}(r)} \times 100\%$$
4. **End-to-End Latency:** The average transit time (in milliseconds) taken by telemetry packets to travel from source motes to the sink.

---

### 4.3 Results

#### Table 4: Performance Summary Across Evaluated Topologies at Rounds 6 and 12
| Metric | Round | Lucas TGO (Proposed) | Equal TGO | Cluster Tree | Mesh Network |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Active Nodes ($N=72$)** | 6 | $\approx 63$ | $\approx 52$ | $\approx 18$ | $\approx 8$ |
| | 12 | $\approx 54$ (75%) | $0$ | $0$ | $0$ |
| **Energy Consumption (J/node)** | 6 | $\approx 0.8$ | $\approx 4.1$ | $\approx 2.2$ | $\approx 2.8$ |
| | 12 | $\approx 1.5$ | $\approx 12.2$ | $\approx 2.2$ (dead) | $\approx 2.8$ (dead) |
| **Packet Delivery Ratio (%)** | 6 | $\approx 96\%$ | $\approx 82\%$ | $\approx 32\%$ | $\approx 10\%$ |
| | 12 | $\approx 91\%$ | $0\%$ | $0\%$ | $0\%$ |
| **End-to-End Latency (ms)** | 6 | $\approx 21$ | $\approx 29$ | $\approx 72$ | $\approx 150$ |
| | 12 | $\approx 25$ | Failed | Failed | Failed |

#### Active Node Retention
All networks began with 72 operational nodes. The unpruned mesh topology deteriorated rapidly under collision overhead and routing churn, retaining only 8 nodes at round 6 and failing entirely by round 7. The cluster tree collapsed shortly after, dropping to 0 functional nodes by round 8 due to cluster-head depletion isolating entire star branches.

Equal TGO maintained better operational stability through round 6 (52 active nodes), but its attrition accelerated in later rounds, leading to complete failure by round 12. In contrast, Lucas TGO degraded gradually, maintaining 63 active nodes at round 6 and 54 nodes ($\approx 75\%$) at round 12.

#### Energy Dissipation
Lucas TGO exhibited the lowest per-node energy expenditure throughout the trial, recording 0.8 J at round 6 and 1.5 J at round 12. Equal TGO climbed to 4.1 J at round 6 and reached 12.2 J by round 12.

The energy dissipation curves for the cluster-tree and mesh networks plateaued at 2.2 J and 2.8 J, respectively, around rounds 7 and 8. These plateaus reflect network extinction rather than energy efficiency; with all nodes dead, no additional energy could be consumed.

#### Packet Delivery Ratio (PDR)
Lucas TGO maintained a reliable delivery ratio between 98% and 91% across all 12 rounds. Equal TGO tracked the proposed system closely during the first two rounds ($\approx 97\%$), but declined to 82% at round 6, dropped to 53% by round 10, and collapsed to 0% at round 12 as its cluster heads failed.

The cluster-tree baseline fell below 50% delivery by round 5, and the unpruned mesh dropped below 50% by round 4.

#### End-to-End Latency
Packet delivery latency for Lucas TGO remained steady throughout the benchmark, rising slightly from 19 ms at round 1 to 25 ms at round 12. Equal TGO delivered lower initial latencies during rounds 1 to 3 (15 ms to 19 ms), but its latency escalated to 29 ms at round 6 and peaked at 85 ms at round 11 before complete failure.

The cluster tree reached 95 ms at round 7, while the mesh network experienced severe contention, peaking near 150 ms at round 6 before losing end-to-end connectivity.

---

### 4.4 Discussion
These results highlight two distinct operational effects:

1. **Impact of Link Pruning:** Comparing the unpruned mesh with Equal TGO demonstrates the value of intra-cluster link optimization. Both configurations share identical 12-node cluster sizes, yet Equal TGO retained more functional nodes, lowered energy drain, and preserved delivery ratios for several rounds longer. Eliminating redundant intra-cluster communication channels suppresses packet collisions and control-message amplification while preserving necessary forwarding paths.
2. **Impact of Lucas-Guided Sizing:** Comparing Equal TGO with Lucas TGO isolates the influence of cluster sizing. Both use identical TGO link pruning, yet Lucas TGO maintained stable operation through round 12, whereas Equal TGO suffered complete structural collapse.

In uniform clusters, all cluster heads handle similar member counts and forward comparable traffic volumes toward the sink, causing them to reach their battery exhaustion thresholds around the same time. Once these heads fail simultaneously, the network partitions rapidly.

Under the Lucas distribution, smaller clusters ($S_1=3, S_2=4$) handle minimal forwarding overhead, preserving low-latency relay bridges toward the sink. Larger clusters ($S_5=18, S_6=29$) leverage their higher internal node density to maintain local detour routes if intermediate forwarders fail. This asymmetry staggers the rate of energy depletion across cluster heads, preventing coordinated network-wide failure.

#### Limitations
These findings reflect an initial evaluation using a 72-node synthetic residential simulation over 12 rounds. While the empirical trends are clear, formal mathematical proofs of TGO convergence bounds, dynamic cluster-head rotation, and tests across physical hardware testbeds under varying traffic bursts remain necessary to establish broader operational bounds.

---

## 5. Conclusion and Future Work

This paper investigated a Lucas sequence-based clustering framework designed to improve fault tolerance and survivability in smart home IoT deployments. By partitioning 72 sensor nodes into six progressively sized clusters ($3, 4, 7, 11, 18, \text{ and } 29$ nodes) combined with Trimetric Graph Optimization and an RPL-UDP collection tree, the architecture staggers energy depletion and maintains routing redundancy.

Under simulated fault injection, the proposed Lucas-TGO system preserved 75% of its sensing nodes through 12 operational rounds, sustained a packet delivery ratio above 90%, kept transit latency below 25 ms, and consumed 1.5 J per node. Under identical experimental conditions, uniform-clustering, cluster-tree, and full-mesh topologies experienced total network failure by round 12.

Planned future work will focus on:
* Validating performance across physical embedded hardware motes using Contiki-NG under real-world interference and non-periodic traffic bursts.
* Developing dynamic cluster-head rotation algorithms and autonomous self-healing routines to extend operational lifespans once primary cluster heads deplete their reserves.
* Evaluating resilience against targeted denial-of-service and routing exhaustion attacks.
* Formulating generalized sequence-based partitioning models for large-scale industrial and municipal IoT deployments exceeding hundreds of nodes.

---

## References

[1] W. B. Nedham and A. K. M. Al-Qurabat, “A comprehensive review of clustering approaches for energy efficiency in wireless sensor networks,” *Int. J. Comput. Appl. Technol.*, vol. 72, no. 2, pp. 139–160, 2023. https://doi.org/10.1504/IJCAT.2023.133035

[2] M. F. Alomari, M. A. Mahmoud, and R. Ramli, “A systematic review on the energy efficiency of dynamic clustering in a heterogeneous environment of wireless sensor networks (WSNs),” *Electronics*, vol. 11, no. 18, p. 2837, 2022. https://doi.org/10.3390/electronics11182837

[3] S. Goel et al., “Energy efficient clustering protocol in wireless sensor networks using an adaptive hybrid optimization algorithm,” *Sci. Rep.*, vol. 16, no. 1, p. 6300, 2026. https://doi.org/10.1038/s41598-026-36957-6

[4] H. Hu, S. Liu, Q. Kang, S. Zhang, and C. Tian, “FGOGNN: An energy-efficient and intelligent cluster-based routing protocol for wireless sensor networks,” *Symmetry*, vol. 18, no. 8, p. 1319, 2026. https://doi.org/10.3390/sym18081319

[5] B. Lonkar, A. Kuthe, P. Charde, A. Dehankar, and R. Kolte, “Optimal hybrid energy-saving cluster head selection for wireless sensor networks: An empirical study,” *Peer-to-Peer Netw. Appl.*, vol. 18, no. 4, p. 182, 2025. https://doi.org/10.1007/s12083-025-02002-y

[6] S. Zhang, X. Liu, and M. Trik, “Energy efficient multi hop clustering using artificial bee colony metaheuristic in WSN,” *Sci. Rep.*, vol. 15, no. 1, p. 26803, 2025. https://doi.org/10.1038/s41598-025-12321-y

[7] B. S. Sukhadeo, S. D. Dhurgude, Y. D. Sinkar, and S. V. Athawale, “A framework of survivability model virtualized wireless sensor networks for IoT-assisted wireless sensor network,” *Internet Technol. Lett.*, vol. 8, no. 2, p. e552, 2025. https://doi.org/10.1002/itl2.552

[8] A. Abdi Seyedkolaei, “Dynamic sink placement in wireless sensor networks for enhancing network lifetime and improving network survivability,” *J. Supercomput.*, vol. 81, no. 8, p. 952, 2025. https://doi.org/10.1007/s11227-025-07395-4

[9] M. Elappila and S. Chinara, “Implementation of survivability aware protocols in WSN for IoT applications using Contiki-OS and hardware testbed evaluation,” *Microprocess. Microsyst.*, vol. 104, p. 104988, 2024. https://doi.org/10.1016/j.micpro.2023.104988

[10] R. F. Mansour et al., “Energy aware fault tolerant clustering with routing protocol for improved survivability in wireless sensor networks,” *Comput. Netw.*, vol. 212, p. 109049, 2022. https://doi.org/10.1016/j.comnet.2022.109049

[11] R. Pietrantuono, M. Ficco, and F. Palmieri, “Survivability analysis of IoT systems under resource exhausting attacks,” *IEEE Trans. Inf. Forensics Security*, vol. 18, pp. 3277–3288, 2023. https://doi.org/10.1109/TIFS.2023.3278449

[12] T. Koshy, *Fibonacci and Lucas Numbers with Applications*. New York, NY, USA: Wiley, 2001.

[13] T. Winter, Ed., P. Thubert, Ed., A. Brandt, J. Hui, R. Kelsey, P. Levis, K. Pister, R. Struik, J.-P. Vasseur, and R. Alexander, “RPL: IPv6 routing protocol for low-power and lossy networks,” Internet Engineering Task Force, RFC 6550, Mar. 2012. https://doi.org/10.17487/RFC6550

[14] B. Lonkar et al., “A review of hybrid clustering and routing protocols for the hotspot problem in wireless sensor networks,” *Peer-to-Peer Netw. Appl.*, vol. 19, no. 1, p. 8, 2026. https://doi.org/10.1007/s12083-025-02135-0

[15] R. Manchanda et al., “Energy-efficient clustering and routing for IoT-enabled healthcare using adaptive fuzzy logic and hybrid optimization,” *Sci. Rep.*, vol. 15, no. 1, p. 34619, 2025. https://doi.org/10.1038/s41598-025-18243-z

[16] A. Koyalil and S. Rajalingam, “Nature-inspired metaheuristic strategies in energy-efficient wireless sensor networks for enhancing network lifetime: A review,” *Wireless Pers. Commun.*, pp. 1–31, 2026. https://doi.org/10.1007/s11277-026-12065-6

[17] X. Yang, W. Zhu, J. Li, X. Zeng, and Y. Qiu, “An adaptive clustering routing algorithm with high survivability based on dynamic hierarchical head backup for underwater optical-acoustic hybrid wireless sensor networks,” *IEEE Sensors J.*, 2026. https://doi.org/10.1109/JSEN.2026.3670110

[18] N. Hegde and P. Amin, “Improvised mobile sink based data survivability in unattended wireless sensor networks,” in *Proc. Int. Conf. ICT Sustain. Dev.*, Cham, Switzerland: Springer, Jul. 2025, pp. 163–172. https://doi.org/10.1007/978-3-032-06694-7_15

[19] M. K. Watfa, “Immune-economic self-healing: A distributed fault-tolerance algorithm for IoT networks,” in *Proc. 9th Int. Conf. Commun. Eng. Technol. (ICCET)*, IEEE, Jun. 2026, pp. 189–197. https://doi.org/10.1109/ICCET70051.2026.11659029

[20] V. Mafeni, P. B. Ta, and Y. Kim, “A dynamic lifecycle-aware disaster recovery framework for stateful IoT applications in edge environments,” *IEEE Access*, vol. 14, pp. 50739–50754, 2026. https://doi.org/10.1109/ACCESS.2026.3679705

[21] P. Rezaeimoghaddam and I. Al-Anbagi, “Heuristic and reinforcement learning-based survivable trust-aware virtual network embedding for IoT networks,” *Ad Hoc Netw.*, vol. 177, p. 103898, 2025. https://doi.org/10.1016/j.adhoc.2025.103898

[22] K. B. Siddiqa et al., “Assessment of survivability and importance analysis for networks managing intricate traffic flows,” *IEEE Commun. Stand. Mag.*, 2025. https://doi.org/10.1109/MCOMSTD.2025.3638981

[23] M. Zekun, W. Minrong, Y. Geng, D. Guangzhi, D. Wenqi, and W. Qipeng, “Enhancing survivability in power IoT systems based on compliance checks,” in *Proc. Asia-Europe Conf. Cybersecurity, Internet Things Soft Comput. (CITSC)*, IEEE, Jan. 2025, pp. 930–935. https://doi.org/10.1109/CITSC64390.2025.00174

[24] Y. Bertrand, J. De Weerdt, and E. Serral, “TROPICCAL: Multi-perspective trace clustering for IoT-enhanced processes,” *Comput. Ind.*, vol. 175, p. 104419, 2026. https://doi.org/10.1016/j.compind.2025.104419

[25] A. M. Khedr and S. Rani S, “Cloud-based congestion-aware data distribution for healthcare IoT using Laplacian kernel clustering and censored weighted queuing,” *Neural Comput. Appl.*, vol. 38, no. 5, p. 117, 2026. https://doi.org/10.1007/s00521-026-11854-1

[26] B. C. da Silva, R. Pereira dos Santos, and D. Viana, “ReqCluster4IoT: A clustering method for functional requirements in Internet of Things applications,” *Requirements Eng.*, vol. 31, no. 2, p. 12, 2026. https://doi.org/10.1007/s00766-026-00467-8
