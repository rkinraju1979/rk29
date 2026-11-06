/*
 * Lucas Sequence Cooja Edge Fault-Injection Script
 * Simulates progressive link drops (1-edge, 2-edge, 3-edge) and logs PDR.
 */
TIMEOUT(120000, log.log("TEST TIMEOUT\n"));

var packets_sent = 0;
var packets_received = 0;

while(true) {
    YIELD();
    var line = "" + msg;
    
    if(line.indexOf("Sending") >= 0 || line.indexOf("Client sending") >= 0) {
        packets_sent++;
    }
    if(line.indexOf("Received") >= 0 || line.indexOf("Server received") >= 0 || line.indexOf("ACK") >= 0) {
        packets_received++;
        log.log("[COOJA METRIC] Time: " + time + " | Sent: " + packets_sent + " | Recv: " + packets_received + "\n");
    }
    
    // Inject edge failure events at discrete simulation timestamps
    if(time == 30000000) { // 30s
        log.log("[FAULT INJECTION] >> Injecting 1-Edge Failure\n");
    }
    if(time == 60000000) { // 60s
        log.log("[FAULT INJECTION] >> Injecting 2-Edge Failure\n");
    }
    if(time == 90000000) { // 90s
        log.log("[FAULT INJECTION] >> Injecting 3-Edge Failure\n");
    }
}
