/*
 * Cooja Automated Test Script for Lucas Clustered RPL-UDP Simulation
 * 
 * Usage in Cooja:
 * - Load in Cooja GUI via: Plugins -> Simulation script editor
 * - Or automatically executed in -nogui headless mode
 */

TIMEOUT(180000, log.log("[COOJA_SIM] Simulation finished after 180s.\n"));

var total_tx = 0;
var total_rx = 0;
var current_round = 0;
var active_nodes = {};
var failovers = 0;

log.log("=================================================================\n");
log.log(" COOJA RPL-UDP LUCAS CLUSTERED SURVIVABILITY BENCHMARK STARTED   \n");
log.log(" Total Nodes: 76 (Node 0 Sink Root + 75 Motes in L0..L7 Clusters)\n");
log.log("=================================================================\n");

while (true) {
  YIELD();

  var line = "" + msg;

  // Intercept Client TX
  if (line.indexOf("[CLIENT_TX]") >= 0) {
    total_tx++;
    active_nodes[id] = true;
  }

  // Intercept Server RX
  if (line.indexOf("[SERVER_RX]") >= 0) {
    total_rx++;
  }

  // Intercept 2-Edge Failover events
  if (line.indexOf("[2-EDGE FAILOVER]") >= 0) {
    failovers++;
    log.log("[COOJA_EVENT] " + line + "\n");
  }

  // Intercept Round Status
  if (line.indexOf("[NODE_STATUS]") >= 0) {
    var parts = line.split("|");
    for (var i = 0; i < parts.length; i++) {
      if (parts[i].indexOf("Round:") >= 0) {
        var r = parseInt(parts[i].replace("Round:", "").trim());
        if (r > current_round) {
          current_round = r;
          
          var livingCount = 0;
          for (var k in active_nodes) {
            if (active_nodes[k]) livingCount++;
          }

          var pdr = total_tx > 0 ? ((total_rx / total_tx) * 100).toFixed(1) : "100.0";
          log.log("[ROUND_METRIC] Round: " + current_round + 
                  " | LivingNodes: " + livingCount + 
                  " | TX: " + total_tx + 
                  " | RX: " + total_rx + 
                  " | PDR: " + pdr + "%" + 
                  " | Failovers: " + failovers + "\n");
        }
      }
    }
  }
}
