# Manual Testing Guide for Agent Pre-initialization

This document describes how to manually test the agent pre-initialization feature.

## What Changed

Previously, agents were created lazily (on-demand) when a user first submitted a question. Now, agents are created asynchronously in the background as soon as the application starts, so they are ready when the user needs them.

## Test Scenarios

### Scenario 1: Normal Startup with Fast Network
**Expected Behavior:**
1. Launch the application with `python run_app.py`
2. You should see "Initializing agents in background..." in the status bar
3. Check the Reasoning tab - you should see "Starting agent initialization in background..."
4. After 30-60 seconds, status changes to "Ready - Agents initialized"
5. Reasoning tab shows "✅ Agent initialization completed - ready to process questions"

### Scenario 2: Submit Question During Initialization
**Expected Behavior:**
1. Launch the application
2. Immediately type a question and click "Ask!" before agents finish initializing
3. The status should show "Processing..." 
4. Reasoning tab should show "Waiting for agent initialization to complete..."
5. After agents are ready, the question processing continues normally
6. You should see a successful answer (assuming valid Azure configuration)

### Scenario 3: Import Excel During Initialization
**Expected Behavior:**
1. Launch the application
2. Immediately click "Import From Excel" before agents finish initializing
3. The Excel file should load and display immediately in the Answer tab
4. Status shows "Spreadsheet loaded - initializing agents..."
5. Reasoning tab shows "Waiting for agent initialization to complete..."
6. After agents are ready, question processing begins automatically

### Scenario 4: Initialization Failure Handling
**Expected Behavior:**
1. Misconfigure the application (e.g., invalid Azure endpoint in .env)
2. Launch the application
3. Status should show "Agent initialization failed"
4. Reasoning tab shows "❌ Agent initialization failed: [error message]"
5. When you try to submit a question, you should get an error message about agent initialization failure

### Scenario 5: Multiple Question Submissions
**Expected Behavior:**
1. Launch the application and wait for agents to initialize
2. Submit a question - should process immediately (no waiting)
3. Submit another question - should also process immediately
4. Agents should remain initialized between questions (no re-initialization)

## Verification Points

### Check Status Bar
- On startup: "Initializing agents in background..."
- After success: "Ready - Agents initialized" (green)
- After failure: "Agent initialization failed" (red)

### Check Reasoning Tab
- Shows timestamp-prefixed messages
- Shows initialization progress messages
- Shows "✅" on success or "❌" on failure

### Check Application Responsiveness
- UI should be responsive during agent initialization
- Should be able to type in the question box immediately
- Should be able to browse UI elements while initializing

### Check Timing
- First question after startup: Should not wait for initialization if already complete
- Question submitted during initialization: Should wait for completion, then process
- Initialization should take approximately 30-60 seconds (typical Azure connection time)

## Common Issues

### Issue: Application hangs on startup
**Possible Cause:** Network connectivity issues or Azure service problems
**Resolution:** Check Azure service status, internet connection, firewall settings

### Issue: Questions submitted immediately fail
**Possible Cause:** Agent initialization failed silently
**Resolution:** Check Reasoning tab for error messages, verify .env configuration

### Issue: Initialization takes longer than 60 seconds
**Possible Cause:** Slow network connection or Azure service latency
**Resolution:** Normal behavior - wait up to 120 seconds total (includes retry logic)

## Configuration Requirements

For testing, ensure you have:
1. Valid `.env` file with Azure AI Foundry configuration
2. `AZURE_AI_FOUNDRY_ENDPOINT` set to your project endpoint
3. `AZURE_AI_FOUNDRY_MODEL_DEPLOYMENT_NAME` set to your model deployment
4. `BING_CONNECTION_ID` set to your Bing search connection
5. Active Azure authentication (`az login` completed successfully)

## Performance Expectations

### Before This Change (Lazy Loading)
- App starts instantly
- First question submission: Wait 30-60 seconds for agent creation + processing time
- Subsequent questions: Fast (agents already created)

### After This Change (Pre-initialization)
- App starts instantly (agents initialize in background)
- First question submission: Fast if agents finished initializing, or wait if still initializing
- Subsequent questions: Fast (agents already created)
- User can start typing immediately upon launch

## Success Criteria

The feature is working correctly if:
1. ✅ Agents start initializing automatically on app launch
2. ✅ Status bar shows initialization progress
3. ✅ Reasoning tab logs initialization steps
4. ✅ Questions can be submitted during initialization (they wait for completion)
5. ✅ Excel imports can be started during initialization (they wait for completion)
6. ✅ After initialization completes, questions process immediately
7. ✅ Initialization failures are handled gracefully with clear error messages
8. ✅ UI remains responsive during initialization
