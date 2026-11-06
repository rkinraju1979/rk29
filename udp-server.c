/**
 * @file udp-server.c
 * @brief Contiki-NG RPL-UDP Root Sink Node (Node 0)
 * 
 * Functions:
 * 1. Initializes as the RPL DAG Root for the 76-node Lucas Clustered Network.
 * 2. Receives round-based telemetry packets from all 8 Lucas clusters.
 * 3. Logs structured metrics: Round, Sender Node ID, Seq Num, and PDR.
 * 4. Sends ACK reply to confirm bidirectional link reliability.
 */

#include "contiki.h"
#include "net/routing/routing.h"
#include "net/netstack.h"
#include "net/ipv6/simple-udp.h"
#include "sys/node-id.h"
#include "sys/log.h"
#include <stdio.h>
#include <string.h>

#define LOG_MODULE "RPL-Root"
#define LOG_LEVEL LOG_LEVEL_INFO

#define UDP_CLIENT_PORT 8765
#define UDP_SERVER_PORT 5678

static struct simple_udp_connection udp_conn;
static uint32_t total_rx_packets = 0;
static uint32_t current_round = 0;
static uint8_t active_senders[76] = {0};

PROCESS(udp_server_process, "RPL Root Sink Node");
AUTOSTART_PROCESSES(&udp_server_process);

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
  uint32_t seq = 0;
  uint16_t sender_id = 0;
  uint32_t round_num = 0;
  char ack_msg[32];

  total_rx_packets++;

  // Parse structured payload: "ID:%u|R:%lu|SEQ:%lu"
  if(sscanf((char *)data, "ID:%hu|R:%lu|SEQ:%lu", &sender_id, (unsigned long *)&round_num, (unsigned long *)&seq) >= 2) {
    if(sender_id < 76) {
      active_senders[sender_id] = 1;
    }
    if(round_num > current_round) {
      current_round = round_num;
    }

    LOG_INFO("[SERVER_RX] Round: %lu | Sender: %u | Seq: %lu | TotalRX: %lu\n",
             (unsigned long)round_num, sender_id, (unsigned long)seq, (unsigned long)total_rx_packets);
  } else {
    LOG_INFO("[SERVER_RX] Raw: '%.*s' (Total: %lu)\n", datalen, (char *)data, (unsigned long)total_rx_packets);
  }

  // Send ACK back to the sender
  snprintf(ack_msg, sizeof(ack_msg), "ACK:%u|R:%lu", sender_id, (unsigned long)current_round);
  simple_udp_sendto(&udp_conn, ack_msg, strlen(ack_msg), sender_addr);
}

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(udp_server_process, ev, data)
{
  static struct etimer periodic_stats_timer;

  PROCESS_BEGIN();

  /* Initialize as RPL DAG Root */
  NETSTACK_ROUTING.root_start();
  LOG_INFO("=== Node %u started as RPL DAG Root Sink ===\n", node_id);

  /* Register UDP server socket */
  simple_udp_register(&udp_conn, UDP_SERVER_PORT, NULL, UDP_CLIENT_PORT, udp_rx_callback);

  /* Periodic statistics logging every 10 seconds */
  etimer_set(&periodic_stats_timer, 10 * CLOCK_SECOND);

  while(1) {
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&periodic_stats_timer));

    uint16_t active_count = 0;
    for(int i = 1; i < 76; i++) {
      if(active_senders[i]) {
        active_count++;
      }
    }

    LOG_INFO("[ROUND_STATS] Round: %lu | ActiveSenders: %u/75 | TotalPackets: %lu | PDR: %.1f%%\n",
             (unsigned long)current_round, active_count, (unsigned long)total_rx_packets,
             active_count > 0 ? (total_rx_packets * 100.0f) / (active_count * (current_round > 0 ? current_round : 1)) : 100.0f);

    etimer_reset(&periodic_stats_timer);
  }

  PROCESS_END();
}
