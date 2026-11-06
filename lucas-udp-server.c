/**
 * @file lucas-udp-server.c
 * @brief Contiki-NG RPL-UDP Gateway Root Server for Lucas 2-Edge Networks
 */

#include "contiki.h"
#include "net/routing/routing.h"
#include "net/netstack.h"
#include "net/ipv6/simple-udp.h"
#include "sys/node-id.h"
#include "sys/log.h"
#include <stdio.h>
#include <string.h>

#define LOG_MODULE "LucasServer"
#define LOG_LEVEL LOG_LEVEL_INFO

#define UDP_CLIENT_PORT 8765
#define UDP_SERVER_PORT 5678

static struct simple_udp_connection udp_conn;

PROCESS(lucas_udp_server_process, "Lucas 2-Edge Root Server");
AUTOSTART_PROCESSES(&lucas_udp_server_process);

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
  char reply[64];
  LOG_INFO("Edge Gateway Node %u received: '%.*s' from ", node_id, datalen, (char *)data);
  LOG_INFO_6ADDR(sender_addr);
  LOG_INFO_("\n");

  // Echo ACK back to client to confirm edge delivery
  snprintf(reply, sizeof(reply), "ACK_GW%u_OK", node_id);
  simple_udp_sendto(&udp_conn, reply, strlen(reply), sender_addr);
}

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(lucas_udp_server_process, ev, data)
{
  PROCESS_BEGIN();

  // Initialize as RPL Root for this gateway domain
  NETSTACK_ROUTING.root_start();

  LOG_INFO("Lucas 2-Edge Gateway Node %u started as RPL Root\n", node_id);

  simple_udp_register(&udp_conn, UDP_SERVER_PORT, NULL, UDP_CLIENT_PORT, udp_rx_callback);

  PROCESS_END();
}
