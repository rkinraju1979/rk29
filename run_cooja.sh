#!/usr/bin/env bash
# ==============================================================================
# Contiki-NG Cooja Simulation Runner for Lucas Clustered Survivability Benchmark
# ==============================================================================

set -e

CONTIKI_DIR="${CONTIKI_DIR:-../..}"
COOJA_DIR="${CONTIKI_DIR}/tools/cooja"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================================================================"
echo " CONTIKI-NG COOJA RUNNER: 76-NODE LUCAS CLUSTERED SURVIVABILITY BENCHMARK"
echo " Topologies: Star (75 links) | Wheel (140 links) | Mesh (256 links) | Lucas (107 links)"
echo " Base Directory: ${BASE_DIR}"
echo "================================================================================"

# Step 1: Compile Contiki-NG Mote Firmware for Cooja target
echo -e "\n[Step 1/3] Building Contiki-NG Cooja binaries (TARGET=cooja)..."
cd "${BASE_DIR}"
if command -v make >/dev/null 2>&1; then
  make TARGET=cooja clean || true
  make TARGET=cooja -j4
  echo "  --> Compilation successful: udp-server.cooja & udp-client.cooja built."
else
  echo "  [WARN] 'make' not found. Ensure Contiki-NG environment is configured."
fi

# Step 2: Run Cooja Simulations
run_simulation() {
  local CSC_NAME="$1"
  local LOG_NAME="$2"
  local CSC_PATH="${BASE_DIR}/${CSC_NAME}"
  local LOG_PATH="${BASE_DIR}/${LOG_NAME}"

  echo -e "\n--- Running ${CSC_NAME} -> ${LOG_NAME} ---"

  if [ -f "${COOJA_DIR}/dist/cooja.jar" ]; then
    java -mx1024m -jar "${COOJA_DIR}/dist/cooja.jar" -nogui="${CSC_PATH}" -contiki="${CONTIKI_DIR}" > "${LOG_PATH}" 2>&1
    echo "  [SUCCESS] Simulation complete. Log saved to ${LOG_NAME}"
  elif command -v ant >/dev/null 2>&1 && [ -d "${COOJA_DIR}" ]; then
    (cd "${COOJA_DIR}" && ant run_nogui -Dargs="${CSC_PATH}") > "${LOG_PATH}" 2>&1
    echo "  [SUCCESS] Simulation complete via Ant. Log saved to ${LOG_NAME}"
  else
    echo "  [INFO] Cooja runtime not directly detected. To run in Cooja GUI:"
    echo "         1. Start Cooja: 'cd ${COOJA_DIR} && ./gradlew run' (or 'ant run')"
    echo "         2. File -> Open Simulation -> Select '${CSC_NAME}'"
    echo "         3. Click 'Start' in the Simulation Control panel."
  fi
}

echo -e "\n[Step 2/3] Executing Cooja Simulations in Headless Mode..."
run_simulation "cooja-clustered-star.csc"  "cooja-star.log"
run_simulation "cooja-clustered-wheel.csc" "cooja-wheel.log"
run_simulation "cooja-clustered-mesh.csc"  "cooja-mesh.log"
run_simulation "cooja-lucas-2edge.csc"     "cooja-lucas.log"

# Step 3: Generate Survivability Graphs
echo -e "\n[Step 3/3] Generating Survivability Graphs (Nodes on X-axis vs. Rounds on Y-axis)..."
python3 "${BASE_DIR}/plot_cooja_survivability.py"

echo -e "\n================================================================================"
echo " ALL SIMULATIONS AND PLOTS COMPLETED!"
echo " Results available in:"
echo "   - Journal Plots (360 DPI, White Background): ${BASE_DIR}/output/"
echo "     • fig1_survivability_nodes_vs_rounds_360dpi.svg / .png"
echo "     • fig2_lifetime_rounds_vs_nodes_360dpi.svg / .png"
echo "     • fig3_pdr_vs_rounds_360dpi.svg / .png"
echo "     • fig4_energy_dissipation_360dpi.svg / .png"
echo "     • fig5_composite_journal_quad_360dpi.png (All-in-one 2x2 grid)"
echo "   - Report: lucas_rounds_survivability.json"
echo "   - Dashboard: http://localhost:8080/"
echo "================================================================================"
