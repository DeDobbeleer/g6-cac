#!/bin/bash
# Commands for Monday Demo with Adriana's team

echo "=========================================="
echo "CaC-ConfigMgr Demo - Bank A Production"
echo "=========================================="
echo ""

# 1. Setup
echo "1. ACTIVER L'ENVIRONNEMENT"
echo "   source venv/bin/activate"
echo ""

# 2. Generate demo
echo "2. GÉNÉRER LA DÉMO"
echo "   cac-configmgr generate-demo --output demo-configs"
echo ""

# 3. Show structure
echo "3. VOIR LA STRUCTURE (4 niveaux)"
echo "   tree demo-configs -L 4"
echo ""

# 4. Validate
echo "4. VALIDATION SYNTAXIQUE"
echo "   cac-configmgr validate demo-configs/"
echo ""

# 5. Plan - The main demo command
echo "5. PLAN - Résolution d'héritage complète"
echo "   cac-configmgr plan \\"
echo "     --fleet demo-configs/instances/banks/bank-a/prod/fleet.yaml \\"
echo "     --topology demo-configs/instances/banks/bank-a/prod/instance.yaml \\"
echo "     --templates-dir demo-configs/templates"
echo ""

# 6. Show resolved payload
echo "6. VOIR LE PAYLOAD API GÉNÉRÉ"
echo "   cat demo-configs/.desired-state/bank-a-prod-api-payload.json | jq ."
echo ""

# 7. Summary of what demo shows
echo "=========================================="
echo "CE QUE LA DÉMO MONTRE:"
echo "=========================================="
echo "• 6 niveaux d'héritage résolus"
echo "• 10 repos, 6 RP, 4 PP, 4 NP, 3 EP"
echo "• Toutes les références cohérentes"
echo "• Chaîne: Repo → RP → NP/EP → PP"
echo "• Variables interpolées ({{mount_point}})"
echo "• Payload API prêt pour DirSync"
echo "=========================================="
