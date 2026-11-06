#ifndef PROJECT_CONF_H_
#define PROJECT_CONF_H_

/* Set to 1 to enable RPL routing */
#define UIP_CONF_ROUTER 1

/* Enable RPL-Lite (default in Contiki-NG) */
#define ROUTING_CONF_RPL_LITE 1

/* Configure CSMA as MAC layer */
#define NETSTACK_CONF_MAC     csma_driver
#define NETSTACK_CONF_RADIO   cooja_radio_driver

/* Increase queue buffers for dense 76-node Lucas network */
#define QUEUEBUF_CONF_NUM 32

/* Enable Energest energy profiling for Contiki motes */
#define ENERGEST_CONF_ON 1

/* UDP Communication Ports */
#define UDP_CLIENT_PORT 8765
#define UDP_SERVER_PORT 5678

/* Default Transmission Interval (Round duration: e.g. 5 seconds) */
#define SEND_INTERVAL (5 * CLOCK_SECOND)

/* Radio transmission power & channel */
#define CC26XX_CONF_RADIO_TX_POWER 0
#define IEEE802154_CONF_PANID 0xabcd
#define IEEE802154_CONF_DEFAULT_CHANNEL 26

#endif /* PROJECT_CONF_H_ */
