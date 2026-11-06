/**
 * @file udp-client.c
 * @brief Contiki-NG RPL-UDP Client for Lucas Clustered & 2-Edge Survivable Networks
 * 
 * Functions:
 * 1. Operates as Sensor Mote or Cluster Head across Lucas Clusters (L0..L7).
 * 2. Transmits 1 telemetry packet per round with jitter.
 * 3. Supports 2-Edge survivability failover via triangle partner when direct CH link fails.
 * 4. Logs Energest radio energy dissipation (TX, RX, CPU, LPM) per round.
 */

#include "contiki.h"
#include "net/routing/routing.h"
#include "random.h"
#include "net/netstack.h"
#include "net/ipv6/simple-udp.h"
#include "sys/node-id.h"
#include "sys/energest.h"
#include "sys/log.h"
#include <stdio.h>
#include <string.h>

#define LOG_MODULE "LucasClient"
#define LOG_LEVEL LOG_LEVEL_INFO

#define UDP_CLIENT_PORT 8765
#define UDP_SERVER_PORT 5678

#define SEND_INTERVAL (5 * CLOCK_SECOND)
#define MAX_MISSED_ACKS 3

static struct simple_udp_connection udp_conn;
static uip_ipaddr_t dest_ipaddr;
static uip_ipaddr_t partner_ipaddr;

static uint32_t round_counter = 0;
static uint32_t seq_counter = 0;
static uint8_t missed_ack_count = 0;
static uint8_t using_backup_path = 0;

/* Cluster Head List for 8 Lucas Clusters: L0..L7 */
static const uint8_t CLUSTER_HEADS[8] = {1, 3, 4, 7, 11, 18, 29, 47};

static int is_cluster_head(uint16_t id) {
  for(int i = 0; i < 8; i++) {
    if(CLUSTER_HEADS[i] == id) return 1;
  }
  return 0;
}

/* Triangle Partner Lookup for 2-Edge Lucas Topology */
static uint16_t get_triangle_partner(uint16_t id) {
  // Cluster L2 = 3 (Nodes 4, 5, 6): Triangle (4, 5, 6)
  if(id == 5) return 6;
  if(id == 6) return 5;
  // Generic pairs in Lucas clusters: (id, id ^ 1)
  if(id >= 7 && id <= 10) {
    if(id == 8) return 9;
    if(id == 9) return 8;
  }
  if(id >= 11 && id <= 17) {
    if(id == 12) return 13;
    if(id == 13) return 12;
    if(id == 14) return 15;
    if(id == 15) return 14;
  }
  if(id >= 18 && id <= 28) {
    if(id == 19) return 20;
    if(id == 20) return 19;
    if(id == 21) return 22;
    if(id == 22) return 21;
    if(id == 23) return 24;
    if(id == 24) return 23;
  }
  if(id >= 29 && id <= 46) {
    if(id >= 30 && (id % 2 == 0)) return id + 1;
    if(id >= 31 && (id % 2 != 0)) return id - 1;
  }
  if(id >= 47 && id <= 75) {
    if(id >= 48 && (id % 2 == 0)) return id + 1;
    if(id >= 49 && (id % 2 != 0)) return id - 1;
  }
  return 0; // No partner
}

PROCESS(udp_client_process, "Lucas Clustered UDP Client");
AUTOSTART_PROCESSES(&udp_client_process);

/*---------------------------------------------------------------------------*/
static void
udp_rx_callback(struct simple_udp_connection *c,
                const uip_ipaddr_t *sender_addr,
                uint16_t sender_port,
                const uip_ipaddr_t *receiver_addr,
                uint16_t receiver_port,
                const uint8_t *data,
                uint16_t datalen)
{
  LOG_INFO("[CLIENT_ACK] Node %u received ACK: '%.*s'\n", node_id, datalen, (char *)data);
  missed_ack_count = 0;
  if(using_backup_path) {
    LOG_INFO("[CLIENT_RECOVERY] Node %u primary link restored!\n", node_id);
    using_backup_path = 0;
  }
}

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(udp_client_process, ev, data)
{
  static struct etimer periodic_timer;
  static char payload[48];
  uint16_t partner_id;

  PROCESS_BEGIN();

  /* Set Root Sink Destination: fd00::1 (Node 0 / Server) */
  uip_ip6addr(&dest_ipaddr, 0xfd00, 0, 0, 0, 0, 0, 0, 1);

  /* Set Partner Address for 2-edge failover */
  partner_id = get_triangle_partner(node_id);
  if(partner_id > 0) {
    uip_ip6addr(&partner_ipaddr, 0xfd00, 0, 0, 0, 0, 0, 0, partner_id);
  }

  /* Register UDP Client Socket */
  simple_udp_register(&udp_conn, UDP_CLIENT_PORT, NULL, UDP_SERVER_PORT, udp_rx_callback);

  /* Initial jitter before starting first round */
  etimer_set(&periodic_timer, (random_rand() % SEND_INTERVAL));

  while(1) {
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&periodic_timer));

    round_counter++;
    seq_counter++;

    /* Energest Radio Energy Profiling */
    energest_flush();
    uint32_t tx_ticks = (uint32_t)energest_type_time(ENERGEST_TYPE_TRANSMIT);
    uint32_t rx_ticks = (uint32_t)energest_type_time(ENERGEST_TYPE_LISTEN);

    LOG_INFO("[NODE_STATUS] Node: %u | CH: %d | Round: %lu | TX_Ticks: %lu | RX_Ticks: %lu | Status: ALIVE\n",
             node_id, is_cluster_head(node_id), (unsigned long)round_counter,
             (unsigned long)tx_ticks, (unsigned long)rx_ticks);

    if(NETSTACK_ROUTING.node_is_reachable()) {
      /* Format structured telemetry packet */
      snprintf(payload, sizeof(payload), "ID:%u|R:%lu|SEQ:%lu",
               node_id, (unsigned long)round_counter, (unsigned long)seq_counter);

      /* 2-Edge Failover Logic */
      if(missed_ack_count >= MAX_MISSED_ACKS && partner_id > 0) {
        using_backup_path = 1;
        LOG_WARN("[2-EDGE FAILOVER] Node %u routing via Triangle Partner %u\n", node_id, partner_id);
        simple_udp_sendto(&udp_conn, payload, strlen(payload), &partner_ipaddr);
      } else {
        LOG_INFO("[CLIENT_TX] Node %u sending to Root Sink (Round %lu, Seq %lu)\n",
                 node_id, (unsigned long)round_counter, (unsigned long)seq_counter);
        simple_udp_sendto(&udp_conn, payload, strlen(payload), &dest_ipaddr);
      }

      missed_ack_count++;
    } else {
      LOG_WARN("[DISCONNECTED] Node %u cannot reach RPL Root (searching...)\n", node_id);
    }

    /* Wait for next round with random jitter to prevent CSMA synchronized collisions */
    etimer_set(&periodic_timer, SEND_INTERVAL + (random_rand() % (CLOCK_SECOND)));
  }

  PROCESS_END();
}
