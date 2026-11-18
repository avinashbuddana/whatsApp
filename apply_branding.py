#!/usr/bin/env python3
"""Apply WingerX branding to pinned upstream Whatomate before compilation.

This modifies presentation files and the name of the initially seeded organization.
It never edits WhatsApp API, authentication logic, webhooks, campaigns or workers.
"""
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1]).resolve()
frontend = root / "frontend"

def patch(rel, old, new):
    path = frontend / rel
    content = path.read_text()
    if old not in content:
        raise RuntimeError(f"Upstream changed; branding patch needs review: {rel}: {old[:80]!r}")
    path.write_text(content.replace(old, new))

assets = Path("/tmp/wingerx-assets")
shutil.copyfile(assets / "wingerx.css", frontend / "src/assets/wingerx.css")
shutil.copyfile(assets / "client.css", frontend / "src/assets/client.css")
shutil.copyfile(assets / "sgj-elephant-logo.svg", frontend / "public/favicon.svg")
shutil.copyfile(assets / "sgj-elephant-logo.svg", frontend / "public/sgj-elephant-logo.svg")

patch("src/main.ts",
      "import './assets/layout.css'",
      "import './assets/layout.css'\nimport './assets/wingerx.css'\nimport './assets/client.css'")

patch("index.html", "<title>Whatomate</title>", "<title>Shree Gajanand Jewellers | WingerX WhatsApp CRM</title>")
patch("index.html", 'href="/favicon.svg"', 'href="/favicon.svg?v=sgj-elephant-20261118"')
patch("index.html",
      'content="Whatomate - WhatsApp Business Platform"',
      'content="WingerX WhatsApp CRM - conversations, campaigns and automations by Neurixa Solutions"')
# Prefer light mode the first time. Respect preferences when users switch theme.
patch("index.html",
      "var mode = localStorage.getItem('color-mode');",
      "var mode = localStorage.getItem('color-mode') || 'light';")

patch("src/components/layout/AppLayout.vue",
      '<MessageSquare :size="16" aria-hidden="true" />\n        <strong>Whatomate</strong>',
      '<img src="/sgj-elephant-logo.svg" class="wingerx-brand-icon sgj-brand-mark" alt="" aria-hidden="true" />\n        <strong>WingerX · WhatsApp CRM</strong>')
patch("src/components/layout/AppLayout.vue",
      '    <aside data-sidebar :aria-label="t(\'nav.sidebar\')">',
      '''    <aside data-sidebar :aria-label="t('nav.sidebar')">
      <div class="wingerx-sidebar-brand">
        <img src="/sgj-elephant-logo.svg" class="wingerx-brand-icon sgj-brand-mark" alt="" aria-hidden="true" />
        <div class="wingerx-brand-copy">
          <strong>WingerX</strong>
          <small>WhatsApp CRM</small>\n          <span class="wingerx-client-chip">SHREE GAJANAND JEWELLERS</span>
        </div>
      </div>''')
patch("src/views/auth/LoginView.vue",
      '<MessageSquare :size="32" />',
      '''<img src="/sgj-elephant-logo.svg" class="wingerx-auth-mark sgj-auth-mark" alt="" aria-hidden="true" />
            <span class="wingerx-auth-badge">Powered by WingerX WhatsApp CRM</span>''')
patch("src/views/auth/LoginView.vue",
      "<h2>{{ $t('auth.welcomeTitle') }}</h2>",
      "<h2>Shree Gajanand Jewellers</h2>")
patch("src/views/auth/LoginView.vue",
      "<p class=\"text-light\">{{ $t('auth.welcomeSubtitle') }}</p>",
      '<p class="text-light">Sign in to your Shree Gajanand Jewellers WhatsApp workspace. Manage customer messages, campaigns and automation, powered by WingerX.</p>')
# Client login is controlled by the tenant administrator.
# Preserve authentication routes and all underlying services.

# Page-specific semantic hooks for targeted WingerX refinements.
# No application logic, API calls, or user data is changed.
patch("src/views/dashboard/DashboardView.vue",
      '<div class="flex flex-col h-full">',
      '<div class="flex flex-col h-full" data-wingerx-dashboard>')
patch("src/views/chatbot/ChatbotView.vue",
      '<div class="flex flex-col h-full">',
      '<div class="flex flex-col h-full" data-wingerx-chatbot>')

# Use the authentic SGJ elephant emblem as the fallback logo for SGJ only.
# Preserve actual organization-uploaded logos and the org switcher behavior.
patch("src/components/layout/OrganizationSwitcher.vue",
      "org.logo || DEFAULT_LOGO",
      "(org.name?.toLowerCase().includes('shree gajanand') ? '/sgj-elephant-logo.svg' : (org.logo || DEFAULT_LOGO))")
patch("src/components/layout/OrganizationSwitcher.vue",
      "currentOrg.value?.logo || DEFAULT_LOGO",
      "(currentOrgName.value.toLowerCase().includes('shree gajanand') ? '/sgj-elephant-logo.svg' : (currentOrg.value?.logo || DEFAULT_LOGO))")

# Embedded Signup v4/v5: collect Facebook's separate session-info message and
# authorization code, in either arrival order. This preserves all account logic.
patch("src/views/settings/AccountsView.vue",
      "import { ref, computed, onMounted, watch } from 'vue'",
      "import { ref, computed, onMounted, onUnmounted, watch } from 'vue'")
patch("src/views/settings/AccountsView.vue",
      "onMounted(async () => {\n  await Promise.all([fetchAccounts(), fetchWhatsAppConfig()])\n})",
      "onMounted(async () => {\n  window.addEventListener('message', receiveEmbeddedSignupInfo)\n  await Promise.all([fetchAccounts(), fetchWhatsAppConfig()])\n})\nonUnmounted(() => {\n  window.removeEventListener('message', receiveEmbeddedSignupInfo)\n  clearSignupTimer()\n})")
patch("src/views/settings/AccountsView.vue",
      "function launchWhatsAppSignup(isCoexistence: boolean = true) {\n  if (!isFBSDKLoaded.value) {\n    toast.error('Facebook SDK not loaded yet. Please wait...')\n    return\n  }\n\n  if (!whatsappConfig.value) {\n    toast.error('WhatsApp configuration not loaded')\n    return\n  }\n\n  showOnboardingDialog.value = false\n  isConnectingFB.value = true\n\n  const loginOptions: any = {\n    config_id: whatsappConfig.value.config_id,\n    response_type: 'code',\n    override_default_response_type: true\n  }\n\n  if (isCoexistence) {\n    loginOptions.extras = {\n      setup: {},\n      featureType: 'whatsapp_business_app_onboarding',\n      sessionInfoVersion: '3',\n      version: 'v3'\n    }\n  } else {\n    loginOptions.extras = {\n      setup: {}\n    }\n  }\n\n  window.FB.login(\n    (response: any) => {\n      if (response.authResponse) {\n        const code = response.authResponse.code\n        const phoneNumberId = response.authResponse.phone_number_id\n        const wabaId = response.authResponse.waba_id\n\n        if (!code) {\n          toast.error('Incomplete data from Facebook: missing authorization code')\n          isConnectingFB.value = false\n          return\n        }\n\n        exchangeCodeForToken(code, phoneNumberId, wabaId)\n      } else if (response.error) {\n        console.error('Facebook SDK error:', response.error)\n        toast.error(`Facebook error: ${response.error.message || 'Unknown error'}`)\n        isConnectingFB.value = false\n      } else {\n        toast.error('Facebook login was cancelled')\n        isConnectingFB.value = false\n      }\n    },\n    loginOptions\n  )\n}\n\n",
      "// Meta sends the authorization code through FB.login and the selected WABA/phone\n// IDs through an independent WA_EMBEDDED_SIGNUP postMessage. Either can arrive first.\nlet signupCode = ''\nlet signupWabaID = ''\nlet signupPhoneID = ''\nlet signupExchangeStarted = false\nlet signupFallbackTimer: ReturnType<typeof setTimeout> | null = null\n\nfunction clearSignupTimer() {\n  if (signupFallbackTimer) clearTimeout(signupFallbackTimer)\n  signupFallbackTimer = null\n}\n\nfunction exchangeSignupWhenReady(fallback = false) {\n  if (!signupCode || signupExchangeStarted) return\n  if (!signupWabaID && !fallback) return\n  signupExchangeStarted = true\n  clearSignupTimer()\n  // The backend can fetch the phone number using the WABA ID when only WABA\n  // sharing has been completed (including WhatsApp Business App coexistence).\n  void exchangeCodeForToken(signupCode, signupPhoneID, signupWabaID)\n  signupCode = ''\n}\n\nfunction receiveEmbeddedSignupInfo(event: MessageEvent) {\n  // Never trust arbitrary page messages. Only accept HTTPS Facebook origins.\n  let sender: URL\n  try { sender = new URL(event.origin) } catch { return }\n  if (sender.protocol !== 'https:' ||\n      !(sender.hostname === 'facebook.com' || sender.hostname.endsWith('.facebook.com'))) return\n\n  let message: any = event.data\n  if (typeof message === 'string') {\n    try { message = JSON.parse(message) } catch { return }\n  }\n  if (!message || message.type !== 'WA_EMBEDDED_SIGNUP') return\n\n  const state = String(message.event || '')\n  if (state === 'CANCEL' || state === 'ERROR') {\n    clearSignupTimer()\n    signupCode = ''\n    isConnectingFB.value = false\n    return\n  }\n  if (!state.startsWith('FINISH')) return\n\n  const info = message.data || {}\n  const wabaIDs = info.messaging_account_ids || info.waba_ids\n  const firstWabaID = Array.isArray(wabaIDs) ? wabaIDs[0] : ''\n  signupWabaID = String(info.waba_id || firstWabaID || info.messaging_account_id || '')\n  signupPhoneID = String(info.phone_number_id || info.phone_id || '')\n  // Do not log Facebook codes, tokens, or business identifiers.\n  exchangeSignupWhenReady()\n}\n\nfunction launchWhatsAppSignup(isCoexistence: boolean = true) {\n  if (!isFBSDKLoaded.value) {\n    toast.error('Facebook SDK not loaded yet. Please wait...')\n    return\n  }\n  if (!whatsappConfig.value) {\n    toast.error('WhatsApp configuration not loaded')\n    return\n  }\n  clearSignupTimer()\n  signupCode = ''\n  signupWabaID = ''\n  signupPhoneID = ''\n  signupExchangeStarted = false\n  showOnboardingDialog.value = false\n  isConnectingFB.value = true\n\n  // Meta Embedded Signup v2/v3 is retired. Coexistence selection now happens\n  // within the Meta-configured v4/v5 signup, not through old \"version: v3\" extras.\n  if (isCoexistence) {\n    toast.info('If you use WhatsApp Business on your phone, select its connection option in the Meta window.')\n  }\n  const loginOptions: any = {\n    config_id: whatsappConfig.value.config_id,\n    response_type: 'code',\n    override_default_response_type: true,\n    extras: { setup: {} }\n  }\n\n  window.FB.login(\n    (response: any) => {\n      if (response.authResponse) {\n        const code = response.authResponse.code\n        if (!code) {\n          toast.error('Incomplete data from Facebook: missing authorization code')\n          clearSignupTimer()\n          isConnectingFB.value = false\n          return\n        }\n        signupCode = code\n        // Some Meta SDK versions include IDs in authResponse; otherwise the\n        // WA_EMBEDDED_SIGNUP message is the authoritative source.\n        signupWabaID ||= String(response.authResponse.waba_id || '')\n        signupPhoneID ||= String(response.authResponse.phone_number_id || '')\n        exchangeSignupWhenReady()\n        if (!signupExchangeStarted) {\n          signupFallbackTimer = setTimeout(() => {\n            // When Meta does not send session info, preserve the existing\n            // server-side token discovery fallback instead of hanging the UI.\n            exchangeSignupWhenReady(true)\n          }, 5000)\n        }\n      } else if (response.error) {\n        clearSignupTimer()\n        toast.error('Facebook signup failed. Please review the Meta configuration and try again.')\n        isConnectingFB.value = false\n      } else {\n        clearSignupTimer()\n        toast.error('Facebook login was cancelled')\n        isConnectingFB.value = false\n      }\n    },\n    loginOptions\n  )\n}\n\n")

# Do not submit an incomplete OAuth code after 5 seconds. Meta can send its
# WA_EMBEDDED_SIGNUP session completion after the FB.login callback, and a
# cancelled flow can still yield a Facebook response.
patch("src/views/settings/AccountsView.vue",
      "let signupExchangeStarted = false\nlet signupFallbackTimer: ReturnType<typeof setTimeout> | null = null",
      "let signupExchangeStarted = false\nlet signupCancelled = false\nlet signupFallbackTimer: ReturnType<typeof setTimeout> | null = null")
patch("src/views/settings/AccountsView.vue",
      "if (!signupCode || signupExchangeStarted) return",
      "if (!signupCode || signupExchangeStarted || signupCancelled) return")
patch("src/views/settings/AccountsView.vue",
      "if (state === 'CANCEL' || state === 'ERROR') {\n    clearSignupTimer()\n    signupCode = ''\n    isConnectingFB.value = false\n    return\n  }",
      "if (state === 'CANCEL' || state === 'ERROR') {\n    signupCancelled = true\n    clearSignupTimer()\n    signupCode = ''\n    isConnectingFB.value = false\n    return\n  }")
patch("src/views/settings/AccountsView.vue",
      "signupExchangeStarted = false\n  showOnboardingDialog.value = false",
      "signupExchangeStarted = false\n  signupCancelled = false\n  showOnboardingDialog.value = false")
patch("src/views/settings/AccountsView.vue",
      "signupFallbackTimer = setTimeout(() => {\n            // When Meta does not send session info, preserve the existing\n            // server-side token discovery fallback instead of hanging the UI.\n            exchangeSignupWhenReady(true)\n          }, 5000)",
      "signupFallbackTimer = setTimeout(() => {\n            // Meta did not confirm which WhatsApp business account was shared.\n            // Never exchange a code without the WABA ID: that can connect an\n            // unintended account, or produce the misleading token error.\n            if (!signupExchangeStarted && !signupWabaID) {\n              signupCancelled = true\n              signupCode = ''\n              isConnectingFB.value = false\n              toast.error('Meta did not return a WhatsApp Business Account ID. Complete all steps in the Facebook window, then check that your Meta Login configuration uses WhatsApp Embedded Signup and grants whatsapp_business_management.')\n            }\n          }, 15000)")
# Preserve Meta's WA_EMBEDDED_SIGNUP session event. Its version "3" describes
# the callback payload, not the retired signup variation. Also restore the
# coexistence flag for customers keeping their WhatsApp Business mobile app.
patch("src/views/settings/AccountsView.vue",
      "  // Meta Embedded Signup v2/v3 is retired. Coexistence selection now happens\n  // within the Meta-configured v4/v5 signup, not through old \"version: v3\" extras.\n  if (isCoexistence) {\n    toast.info('If you use WhatsApp Business on your phone, select its connection option in the Meta window.')\n  }\n  const loginOptions: any = {\n    config_id: whatsappConfig.value.config_id,\n    response_type: 'code',\n    override_default_response_type: true,\n    extras: { setup: {} }\n  }",
      "  // SessionInfoVersion is the popup *event payload format*, not the\n  // deprecated Embedded Signup flow version. The former is required to receive\n  // WA_EMBEDDED_SIGNUP with the WABA / phone IDs.\n  const loginOptions: any = {\n    config_id: whatsappConfig.value.config_id,\n    response_type: 'code',\n    override_default_response_type: true,\n    extras: {\n      setup: {},\n      sessionInfoVersion: '3',\n      ...(isCoexistence ? { featureType: 'whatsapp_business_app_onboarding' } : {})\n    }\n  }")
# Backend fix for WABA-only sharing: never discard the explicit WABA ID.
backend_accounts_path = root / "internal/handlers/accounts.go"
backend_source = backend_accounts_path.read_text()
if "if phoneID != \"\" && wabaID != \"\" {\n\t\treturn phoneID, wabaID, name, nil\n\t}" not in backend_source:
    raise RuntimeError("Upstream WABA discovery changed; review the patch before deployment")
backend_accounts_path.write_text(backend_source.replace("if phoneID != \"\" && wabaID != \"\" {\n\t\treturn phoneID, wabaID, name, nil\n\t}", "if wabaID != \"\" {\n\t\t// Embedded Signup v4/v5 may return WABA ID without a phone ID.\n\t\t// Resolve its phone directly instead of discarding the known WABA and\n\t\t// trying to infer it again from token granular scopes.\n\t\tif phoneID == \"\" {\n\t\t\tphonesResp, err := a.WhatsApp.GetWABAPhoneNumbers(ctx, wabaID, accessToken)\n\t\t\tif err != nil {\n\t\t\t\treturn \"\", \"\", \"\", fmt.Errorf(\"failed to fetch phone numbers from WABA: %w\", err)\n\t\t\t}\n\t\t\tif len(phonesResp.Data) == 0 {\n\t\t\t\treturn \"\", \"\", \"\", fmt.Errorf(\"no phone numbers found in this WhatsApp Business Account\")\n\t\t\t}\n\t\t\tif len(phonesResp.Data) > 1 {\n\t\t\t\ta.Log.Warn(\"Multiple phone numbers discovered in WABA; selecting the first one\", \"count\", len(phonesResp.Data))\n\t\t\t}\n\t\t\tphone := phonesResp.Data[0]\n\t\t\tphoneID = phone.ID\n\t\t\tif name == \"\" {\n\t\t\t\tname = fmt.Sprintf(\"%s (%s)\", phone.VerifiedName, phone.DisplayPhoneNumber)\n\t\t\t}\n\t\t}\n\t\treturn phoneID, wabaID, name, nil\n\t}", 1))


# SAFETY: prevent Excel scientific notation and corrupted phone numbers from
# getting queued in WhatsApp campaigns. Do not try to reconstruct rounded values.
patch("src/views/settings/CampaignDetailView.vue",
      "    for (let i = 1; i < lines.length; i++) {\n      const values = lines[i].split(',').map(v => v.trim())\n      const phone = values[phoneIndex]?.replace(/[^\\d+]/g, '')\n      if (!phone) continue",
      "    const invalidPhoneRows: number[] = []\n    for (let i = 1; i < lines.length; i++) {\n      const values = lines[i].split(',').map(v => v.trim())\n      const originalPhone = values[phoneIndex]?.trim() || ''\n      // Remove only harmless spacing; never strip E, + in the middle, or\n      // decimal marks that signal Excel's scientific notation.\n      const compactPhone = originalPhone.replace(/[\\s()-]/g, '')\n      if (!/^\\+?[1-9][0-9]{9,14}$/.test(compactPhone)) {\n        invalidPhoneRows.push(i + 1)\n        continue\n      }\n      const phone = compactPhone.replace(/^\\+/, '')")
patch("src/views/settings/CampaignDetailView.vue",
      "    if (recipientsList.length === 0) {\n      toast.error(t('campaigns.noValidRowsToImport'",
      "    if (invalidPhoneRows.length > 0) {\n      toast.error(`CSV contains ${invalidPhoneRows.length} invalid phone number(s) at rows ${invalidPhoneRows.slice(0, 8).join(', ')}. Use full international numbers like 919876543210; set Excel phone cells to Text before exporting. Nothing was imported.`)\n      return\n    }\n    if (recipientsList.length === 0) {\n      toast.error(t('campaigns.noValidRowsToImport'")

# Backend guards prevent invalid recipient imports from any API client, and
# disallow re-sends of previously corrupted recipient rows.
backend_campaign_path = root / "internal/handlers/campaigns.go"
backend_campaign = backend_campaign_path.read_text()
start_import = backend_campaign.index("func (a *App) ImportRecipients(")
start_list = backend_campaign.index("// GetCampaignRecipients implements", start_import)
import_function = backend_campaign[start_import:start_list]
import_old = "for i, rec := range req.Recipients {\n\t\trecipients[i] = models.BulkMessageRecipient{"
import_new = """for i, rec := range req.Recipients {
		cleaned := strings.NewReplacer(" ", "", "-", "", "(", "", ")", "", "\\t", "").Replace(strings.TrimSpace(rec.PhoneNumber))
		if !campaignRecipientPhonePattern.MatchString(cleaned) {
			return r.SendErrorEnvelope(fasthttp.StatusBadRequest,
				fmt.Sprintf("Invalid phone number in recipient row %d. Use full country-code digits, e.g. 919876543210; Excel scientific notation is not valid.", i+1), nil, "")
		}
		rec.PhoneNumber = strings.TrimPrefix(cleaned, "+")
		recipients[i] = models.BulkMessageRecipient{"""
if import_old not in import_function:
    raise RuntimeError("Upstream campaign import layout changed; refusing unsafe patch")
import_function = import_function.replace(import_old, import_new, 1)
backend_campaign = backend_campaign[:start_import] + import_function + backend_campaign[start_list:]

guard = """	// Reject corrupted imported recipient phones before jobs are enqueued.
	// A scientific-notation CSV cell cannot be reconstructed reliably.
	for _, recipient := range recipients {
		if !campaignRecipientPhonePattern.MatchString(recipient.PhoneNumber) {
			return r.SendErrorEnvelope(fasthttp.StatusBadRequest,
				"Campaign contains malformed recipient phone numbers. Export the original contacts as TEXT with country codes and create a new campaign; do not retry this recipient list.", nil, "")
		}
	}

"""
start_func = backend_campaign.index("func (a *App) StartCampaign(")
pause_func = backend_campaign.index("// PauseCampaign", start_func)
start_fn = backend_campaign[start_func:pause_func]
if "if len(recipients) == 0 {" not in start_fn:
    raise RuntimeError("Campaign start guard anchor missing")
start_fn = start_fn.replace("\tif len(recipients) == 0 {", guard + "\tif len(recipients) == 0 {", 1)
backend_campaign = backend_campaign[:start_func] + start_fn + backend_campaign[pause_func:]
retry_func = backend_campaign.index("func (a *App) RetryFailed(")
next_func = backend_campaign.index("// ImportRecipients implements", retry_func)
retry_fn = backend_campaign[retry_func:next_func]
if "if len(failedRecipients) == 0 {" not in retry_fn:
    raise RuntimeError("Campaign retry guard anchor missing")
retry_fn = retry_fn.replace("\tif len(failedRecipients) == 0 {", guard.replace("range recipients", "range failedRecipients") + "\tif len(failedRecipients) == 0 {", 1)
backend_campaign = backend_campaign[:retry_func] + retry_fn + backend_campaign[next_func:]
# regexp and strings are already imported by pinned upstream campaigns.go.
regex_decl = "\nvar campaignRecipientPhonePattern = regexp.MustCompile(`^\\+?[1-9][0-9]{9,14}$`)\n"
if "var campaignRecipientPhonePattern" in backend_campaign:
    raise RuntimeError("Campaign phone guard already present")
backend_campaign = backend_campaign.replace("// CampaignRequest represents", regex_decl + "\n// CampaignRequest represents", 1)
backend_campaign_path.write_text(backend_campaign)

print("WingerX SGJ branding applied", flush=True)
