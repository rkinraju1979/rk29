/**
 * @file lucas-udp-client.c
 * @brief Contiki-NG Dual-Homed RPL-UDP Client for Lucas Sequence 2-Edge Survivable Networks
 * 
 * Supports 2-edge survivability by maintaining active communication with dual Edge Gateways:
 *   - Primary Edge Gateway:   fd00::1 (Port 5678)
 *   - Secondary Edge Gateway: fd00::2 (Port 5678)
 * 
 * If primary edge link degrades or fails, traffic automatically fails over to the secondary
 * edge gateway via alternate edge-disjoint RPL paths.
 */

#include "contiki.h"
#include "net/routing/routing.h"
#include "random.h"
#include "net/netstack.h"
#include "net/ipv6/simple-udp.h"
#include "sys/node-id.h"
#include "sys/log.h"
#include <stdio.h>
#include <string.h>

#define LOG_MODULE "LucasClient"
#define LOG_LEVEL LOG_LEVEL_INFO

#define UDP_CLIENT_PORT 8765
#define UDP_SERVER_PORT 5678
#define SEND_INTERVAL   (2 * CLOCK_SECOND)
#define MAX_MISSED_ACKS 3

static struct simple_udp_connection udp_conn;
static uip_ipaddr_t edge_gw_primary;
static uip_ipaddr_t edge_gw_secondary;
static uint8_t active_gateway_index = 0; // 0 = Primary (fd00::1), 1 = Secondary (fd00::2)
static uint8_t missed_ack_counter = 0;
static uint32_t seq_num = 0;

PROCESS(lucas_udp_client_process, "Lucas 2-Edge Client");
AUTOSTART_PROCESSES(&lucas_udp_client_process);

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
  LOG_INFO("ACK received from Edge Gateway ");
  LOG_INFO_6ADDR(sender_addr);
  LOG_INFO_(": '%.*s'\n", datalen, (char *)data);

  // Reset missed ACK counter on successful reply
  missed_ack_counter = 0;
}

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(lucas_udp_client_process, ev, data)
{
  static struct etimer periodic_timer;
  static char payload[64];
  uip_ipaddr_t *target_gw;

  PROCESS_BEGIN();

  // Initialize Dual Edge Gateway addresses
  uip_ip6addr(&edge_gw_primary,   0xfd00, 0, 0, 0, 0, 0, 0, 1);
  uip_ip6addr(&edge_gw_secondary, 0xfd00, 0, 0, 0, 0, 0, 0, 2);

  // Register UDP socket
  simple_udp_register(&udp_conn, UDP_CLIENT_PORT, NULL, UDP_SERVER_PORT, udp_rx_callback);

  etimer_set(&periodic_timer, random_rand() % SEND_INTERVAL);

  while(1) {
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&periodic_timer));

    if(NETSTACK_ROUTING.node_is_reachable()) {
      seq_num++;

      // Check if primary edge link has failed (2-edge survivability trigger)
      if(missed_ack_counter >= MAX_MISSED_ACKS) {
        active_gateway_index = (active_gateway_index == 0) ? 1 : 0;
        missed_ack_counter = 0;
        LOG_WARN("2-Edge Failover Triggered! Switching active path to Gateway %s\n",
                 active_gateway_index == 0 ? "1 (fd00::1)" : "2 (fd00::2)");
      }

      target_gw = (active_gateway_index == 0) ? &edge_gw_primary : &edge_gw_secondary;

      snprintf(payload, sizeof(payload), "Node %u: Lucas pkt %lu via GW-%u",
               node_id, (unsigned long)seq_num, active_gateway_index + 1);

      LOG_INFO("Sending to Edge GW %u [", active_gateway_index + 1);
      LOG_INFO_6ADDR(target_gw);
      LOG_INFO_("]: '%s'\n", payload);

      simple_udp_sendto(&udp_conn, payload, strlen(payload), target_gw);
      missed_ack_counter++;
    } else {
      LOG_INFO("RPL routing path establishing...\n");
    }

    // Schedule next transmission with collision-avoidance jitter
    etimer_set(&periodic_timer, SEND_INTERVAL - CLOCK_SECOND + (random_rand() % (2 * CLOCK_SECOND)));
  }

  PROCESS_END();
}
