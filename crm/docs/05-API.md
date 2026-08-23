# مرجع الـAPI — NebrasCRM

**188 نقطة نهاية**. توثيق تفاعلي كامل على `/docs` (Swagger).

## المصادقة

| البوابة | الترويسة | الحصول على الرمز |
|---|---|---|
| الموظفون | `Authorization: Bearer <token>` | `POST /api/auth/login` |
| العملاء | `Authorization: Bearer <token>` | `POST /portal/api/login` |
| الشركاء | `Authorization: Bearer <token>` | `POST /agent/api/login` |
| تكاملات | `X-API-Key: nx_...` | من شاشة التكاملات |

---

## الأعمال — CRUD والتحليلات  (87)

| Method | المسار | الدالة | الملف |
|---|---|---|---|
| `GET` | `/api/360/{module}/{rid}` | `view360` | platform_ext.py |
| `GET` | `/api/analytics/dashboard` | `dashboard` | main.py |
| `GET` | `/api/analytics/report` | `report` | main.py |
| `POST` | `/api/auth/login` | `login` | main.py |
| `GET` | `/api/auth/me` | `me` | main.py |
| `GET` | `/api/dashboards` | `list_dash` | platform_ext.py |
| `POST` | `/api/dashboards` | `save_dash` | platform_ext.py |
| `DELETE` | `/api/dashboards/{did}` | `del_dash` | platform_ext.py |
| `GET` | `/api/email/outbox` | `outbox` | mailer.py |
| `POST` | `/api/email/send` | `compose` | mailer.py |
| `GET` | `/api/email/settings` | `get_settings` | mailer.py |
| `PUT` | `/api/email/settings` | `set_settings` | mailer.py |
| `GET` | `/api/email/templates` | `tpls` | mailer.py |
| `PUT` | `/api/email/templates/{tid}` | `upd_tpl` | mailer.py |
| `POST` | `/api/email/test` | `test_mail` | mailer.py |
| `GET` | `/api/email/thread/{module}/{rid}` | `thread` | mailer.py |
| `GET` | `/api/geo/districts` | `districts` | geo.py |
| `GET` | `/api/geo/governorates` | `governorates` | geo.py |
| `GET` | `/api/geo/levels` | `levels` | geo.py |
| `GET` | `/api/geo/quarters` | `quarters` | geo.py |
| `POST` | `/api/geo/quarters` | `add_quarter` | geo.py |
| `GET` | `/api/geo/search` | `geo_search` | geo.py |
| `GET` | `/api/geo/stats` | `stats` | geo.py |
| `GET` | `/api/geo/streets` | `streets` | geo.py |
| `POST` | `/api/geo/streets` | `add_street` | geo.py |
| `GET` | `/api/geo/territories` | `list_terr` | geo.py |
| `POST` | `/api/geo/territories` | `add_terr` | geo.py |
| `DELETE` | `/api/geo/territories/{tid}` | `del_terr` | geo.py |
| `GET` | `/api/geo/uzlah` | `uzlah` | geo.py |
| `GET` | `/api/geo/villages` | `villages` | geo.py |
| `GET` | `/api/intel/battlecard/{cid}` | `battlecard` | intel.py |
| `GET` | `/api/intel/dashboard` | `intel_dashboard` | intel.py |
| `GET` | `/api/intel/matrix` | `matrix` | intel.py |
| `POST` | `/api/interactions` | `add_interaction` | platform_ext.py |
| `GET` | `/api/interactions/stats` | `interaction_stats` | platform_ext.py |
| `POST` | `/api/items/{module}/{rid}` | `save_items` | main.py |
| `POST` | `/api/leads/{rid}/convert` | `convert` | main.py |
| `GET` | `/api/loyalty/member/{member_type}/{mid}` | `member` | loyalty.py |
| `GET` | `/api/loyalty/members` | `members` | loyalty.py |
| `GET` | `/api/loyalty/program` | `program` | loyalty.py |
| `POST` | `/api/loyalty/recompute` | `recompute` | loyalty.py |
| `POST` | `/api/loyalty/redeem` | `redeem` | loyalty.py |
| `GET` | `/api/loyalty/summary` | `summary` | loyalty.py |
| `GET` | `/api/meta` | `meta` | main.py |
| `POST` | `/api/notes/{module}/{rid}` | `add_note` | main.py |
| `GET` | `/api/notifications` | `notifs` | main.py |
| `POST` | `/api/notifications/read` | `read_notifs` | main.py |
| `GET` | `/api/opportunities/analytics` | `opp_analytics` | segments.py |
| `POST` | `/api/opportunities/{oid}/convert` | `convert_opp` | segments.py |
| `GET` | `/api/partners` | `list_partners` | partners.py |
| `POST` | `/api/partners` | `create_partner` | partners.py |
| `POST` | `/api/partners/accrue` | `accrue` | partners.py |
| `GET` | `/api/partners/analytics/summary` | `summary` | partners.py |
| `GET` | `/api/partners/meta` | `meta` | partners.py |
| `POST` | `/api/partners/txn` | `add_txn` | partners.py |
| `DELETE` | `/api/partners/{aid}` | `del_partner` | partners.py |
| `GET` | `/api/partners/{aid}` | `get_partner` | partners.py |
| `PUT` | `/api/partners/{aid}` | `update_partner` | partners.py |
| `GET` | `/api/partners/{aid}/statement` | `statement` | partners.py |
| `GET` | `/api/payments` | `list_payments` | payments.py |
| `GET` | `/api/payments/by-channel` | `by_channel` | payments.py |
| `GET` | `/api/payments/channels` | `list_channels` | payments.py |
| `POST` | `/api/payments/link` | `make_link` | payments.py |
| `POST` | `/api/payments/manual` | `manual` | payments.py |
| `GET` | `/api/payments/summary` | `psummary` | payments.py |
| `GET` | `/api/payments/{pid}/events` | `events` | payments.py |
| `POST` | `/api/payments/{pid}/refund` | `refund` | payments.py |
| `POST` | `/api/payments/{pid}/settle` | `settle` | payments.py |
| `GET` | `/api/search` | `global_search` | main.py |
| `POST` | `/api/segments/apply` | `apply` | segments.py |
| `GET` | `/api/segments/blacklist-check/{account_id}` | `blacklist_check` | segments.py |
| `GET` | `/api/segments/list/{name}` | `list_members` | segments.py |
| `GET` | `/api/segments/meta` | `meta` | segments.py |
| `GET` | `/api/segments/scores` | `scores` | segments.py |
| `POST` | `/api/segments/tag` | `tag` | segments.py |
| `GET` | `/api/tickets/{tid}/portal-thread` | `thread` | portal.py |
| `POST` | `/api/tickets/{tid}/portal-thread` | `staff_reply` | portal.py |
| `GET` | `/api/timeline` | `timeline` | main.py |
| `GET` | `/api/widget` | `widget` | platform_ext.py |
| `GET` | `/api/{module}` | `list_records` | main.py |
| `POST` | `/api/{module}` | `create_record` | main.py |
| `POST` | `/api/{module}/bulk` | `bulk` | main.py |
| `GET` | `/api/{module}/export/csv` | `export_csv` | main.py |
| `POST` | `/api/{module}/import` | `import_csv` | main.py |
| `DELETE` | `/api/{module}/{rid}` | `delete_record` | main.py |
| `GET` | `/api/{module}/{rid}` | `get_record` | main.py |
| `PUT` | `/api/{module}/{rid}` | `update_record` | main.py |

## الذكاء الاصطناعي — AI  (11)

| Method | المسار | الدالة | الملف |
|---|---|---|---|
| `GET` | `/api/ai/churn-risk` | `churn` | ai.py |
| `GET` | `/api/ai/deal/{did}` | `deal_ai` | ai.py |
| `GET` | `/api/ai/digest` | `digest` | ai.py |
| `GET` | `/api/ai/forecast` | `get_forecast` | ai.py |
| `POST` | `/api/ai/generate-email` | `gen` | ai.py |
| `GET` | `/api/ai/lead-score/{lid}` | `lead_score` | ai.py |
| `GET` | `/api/ai/lead-scores` | `lead_scores` | ai.py |
| `GET` | `/api/ai/next-best-action/{module}/{rid}` | `nba` | ai.py |
| `GET` | `/api/ai/pipeline-health` | `pipeline_health` | ai.py |
| `GET` | `/api/ai/status` | `status` | ai.py |
| `POST` | `/api/ai/summarize` | `do_sum` | ai.py |

## التقارير — Reports  (7)

| Method | المسار | الدالة | الملف |
|---|---|---|---|
| `GET` | `/api/reports/catalogue` | `catalogue` | reports.py |
| `GET` | `/api/reports/export/{code}.{fmt}` | `export` | reports.py |
| `GET` | `/api/reports/run/{code}` | `run` | reports.py |
| `GET` | `/api/reports/stagnant-customers` | `stagnant_customers` | segments.py |
| `GET` | `/api/reports/stagnant-products` | `stagnant_products` | segments.py |
| `GET` | `/api/settings/all` | `all_settings` | reports.py |
| `PUT` | `/api/settings/all` | `save_settings` | reports.py |

## الدفع — Payments  (4)

| Method | المسار | الدالة | الملف |
|---|---|---|---|
| `GET` | `/pay/api/channels` | `channels` | payments.py |
| `GET` | `/pay/api/{token}` | `checkout_info` | payments.py |
| `POST` | `/pay/api/{token}/confirm` | `confirm` | payments.py |
| `POST` | `/pay/webhook` | `webhook` | payments.py |

## بوابة العملاء — Customer Portal  (19)

| Method | المسار | الدالة | الملف |
|---|---|---|---|
| `GET` | `/portal/api/document/{kind}/{did}` | `pdocument` | portal.py |
| `GET` | `/portal/api/documents` | `pdocuments` | portal.py |
| `GET` | `/portal/api/invoices` | `pinvoices` | portal.py |
| `POST` | `/portal/api/login` | `plogin` | portal.py |
| `GET` | `/portal/api/loyalty` | `ployalty` | portal.py |
| `GET` | `/portal/api/me` | `pme` | portal.py |
| `GET` | `/portal/api/orders` | `porders` | portal.py |
| `POST` | `/portal/api/orders` | `pnew_order` | portal.py |
| `POST` | `/portal/api/password` | `pchange` | portal.py |
| `GET` | `/portal/api/products` | `pproducts` | portal.py |
| `PUT` | `/portal/api/profile` | `pprofile` | portal.py |
| `GET` | `/portal/api/quotes` | `pquotes` | portal.py |
| `POST` | `/portal/api/quotes/{qid}/decision` | `pquote_decision` | portal.py |
| `GET` | `/portal/api/statement` | `pstatement` | portal.py |
| `GET` | `/portal/api/summary` | `psummary` | portal.py |
| `GET` | `/portal/api/tickets` | `ptickets` | portal.py |
| `POST` | `/portal/api/tickets` | `pnew_ticket` | portal.py |
| `GET` | `/portal/api/tickets/{tid}` | `pticket` | portal.py |
| `POST` | `/portal/api/tickets/{tid}/reply` | `preply` | portal.py |

## بوابة الشركاء — Partner Portal  (14)

| Method | المسار | الدالة | الملف |
|---|---|---|---|
| `GET` | `/agent/api/customers` | `acustomers` | agentportal.py |
| `GET` | `/agent/api/deals` | `adeals` | agentportal.py |
| `GET` | `/agent/api/leads` | `aleads` | agentportal.py |
| `POST` | `/agent/api/leads` | `anew_lead` | agentportal.py |
| `POST` | `/agent/api/login` | `alogin` | agentportal.py |
| `GET` | `/agent/api/loyalty` | `aloyalty` | agentportal.py |
| `GET` | `/agent/api/me` | `ame` | agentportal.py |
| `POST` | `/agent/api/password` | `apassword` | agentportal.py |
| `GET` | `/agent/api/requests` | `arequests` | agentportal.py |
| `POST` | `/agent/api/requests` | `anew_request` | agentportal.py |
| `GET` | `/agent/api/statement` | `astatement` | agentportal.py |
| `GET` | `/agent/api/stock` | `astock` | agentportal.py |
| `GET` | `/agent/api/summary` | `asummary` | agentportal.py |
| `GET` | `/agent/api/territories` | `aterritories` | agentportal.py |

## الإدارة — Administration  (24)

| Method | المسار | الدالة | الملف |
|---|---|---|---|
| `GET` | `/api/admin/users` | `users` | main.py |
| `POST` | `/api/admin/users` | `create_user` | main.py |
| `PUT` | `/api/admin/users/{uid}` | `update_user` | main.py |
| `GET` | `/api/admin/workflows` | `get_wf` | main.py |
| `POST` | `/api/admin/workflows` | `add_wf` | main.py |
| `DELETE` | `/api/admin/workflows/{wid}` | `del_wf` | main.py |
| `GET` | `/api/agent-access` | `list_access` | agentportal.py |
| `POST` | `/api/agent-access` | `grant` | agentportal.py |
| `DELETE` | `/api/agent-access/{uid}` | `del_access` | agentportal.py |
| `PUT` | `/api/agent-access/{uid}` | `upd_access` | agentportal.py |
| `GET` | `/api/agent-requests` | `staff_requests` | agentportal.py |
| `POST` | `/api/agent-requests/{rid}/decide` | `decide` | agentportal.py |
| `GET` | `/api/custom-fields` | `list_cf` | platform_ext.py |
| `POST` | `/api/custom-fields` | `add_cf` | platform_ext.py |
| `DELETE` | `/api/custom-fields/{cid}` | `del_cf` | platform_ext.py |
| `GET` | `/api/integrations` | `list_int` | platform_ext.py |
| `PUT` | `/api/integrations/{code}` | `toggle_int` | platform_ext.py |
| `GET` | `/api/keys` | `list_keys` | platform_ext.py |
| `POST` | `/api/keys` | `create_key` | platform_ext.py |
| `DELETE` | `/api/keys/{kid}` | `del_key` | platform_ext.py |
| `GET` | `/api/portal-access` | `list_access` | portal.py |
| `POST` | `/api/portal-access` | `grant` | portal.py |
| `DELETE` | `/api/portal-access/{pid}` | `del_access` | portal.py |
| `PUT` | `/api/portal-access/{pid}` | `upd_access` | portal.py |

## ويب هوكس — Inbound Webhooks  (3)

| Method | المسار | الدالة | الملف |
|---|---|---|---|
| `POST` | `/api/hooks/leadform` | `hook_leadform` | platform_ext.py |
| `POST` | `/api/hooks/order` | `hook_order` | platform_ext.py |
| `POST` | `/api/hooks/whatsapp` | `hook_whatsapp` | platform_ext.py |

## API عام — Public API  (2)

| Method | المسار | الدالة | الملف |
|---|---|---|---|
| `GET` | `/api/v1/{module}` | `public_list` | platform_ext.py |
| `POST` | `/api/v1/{module}` | `public_create` | platform_ext.py |

## صفحات وملفات — Pages & Assets  (17)

| Method | المسار | الدالة | الملف |
|---|---|---|---|
| `GET` | `/` | `landing` | main.py |
| `GET` | `/agent` | `agent_index` | agentportal.py |
| `GET` | `/agent.js` | `agent_js` | agentportal.py |
| `GET` | `/app` | `index` | main.py |
| `GET` | `/app.js` | `appjs` | main.py |
| `GET` | `/brand/{sub}/{name}` | `brandfile` | main.py |
| `GET` | `/favicon.ico` | `favicon` | main.py |
| `GET` | `/font-check` | `fontcheck` | main.py |
| `GET` | `/fonts/{name}` | `fontfile` | main.py |
| `GET` | `/offline` | `offline_page` | main.py |
| `GET` | `/portal` | `portal_index` | portal.py |
| `GET` | `/portal.js` | `portal_js` | portal.py |
| `GET` | `/pwa.js` | `pwa_js` | main.py |
| `GET` | `/site.webmanifest` | `webmanifest` | main.py |
| `GET` | `/styles.css` | `css` | main.py |
| `GET` | `/sw.js` | `service_worker` | main.py |
| `GET` | `/theme-check` | `themecheck` | main.py |
