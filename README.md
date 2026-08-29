# AppWash Home Assistant Integration  
Monitor AppWash (Miele MOVE) laundry machines from Home Assistant.  
![Python versions](https://img.shields.io/pypi/pyversions/tplinkrouterc6u)

---

### Features  
- **Machine Availability:** See which washing machines and dryers are `FREE` and which are `OCCUPIED`.  
- **Cycle Details:** The active cycle (id, order, product type, timestamps) is exposed as attributes on the machine it runs on.  
- **Estimated Finish Time:** `estimated_end` and `remaining_minutes` are derived from the occupancy window reported by the API.  
- **Wallet Balance:** Your prepaid balance as a sensor.  
- **UI Configuration:** Credentials are entered in the Home Assistant config flow; no YAML.  

---

### ⚠️ Upgrading from 2.1.0

- The device is now named **AppWash** instead of the location, which shortens
  every entity's friendly name. Entity IDs are unchanged.
- Five attributes were removed as duplicates or constants: `machine_name`
  (same as `machine_code`), `location_name` (already in the friendly name),
  `price_type` (always `FIX_PRICE`), `cycle_duration_minutes` (always the
  backend's fixed 120-minute window) and `is_own_cycle` (use
  `occupied_by == 'you'`).

---

### ⚠️ Upgrading from 1.x

AppWash migrated to the Miele MOVE API (`https://www.miele-move.com/appwash/api/app/v1`)
with Amazon Cognito login. Version 2.0.0 follows that migration:

- Entity IDs, entity names and unique IDs are **unchanged**.
- Machine sensor states now use the values the API reports: **`FREE`** (previously
  `AVAILABLE`) and **`OCCUPIED`**, plus **`YOUR_CYCLE`** when the running cycle
  is yours. Dashboard templates comparing against `AVAILABLE` must be updated, and
  a template that checks for `OCCUPIED` will not match your own machine — see the
  example below.
- Existing config entries keep working; the location is resolved automatically
  from your account and can be overridden in the integration options.

---

### Prerequisites  
- A working Home Assistant instance.  
- Valid AppWash account credentials (the same ones used on <https://web.appwash.com>).  
- Internet connectivity to `www.miele-move.com` and `appwash.auth.eu-north-1.amazoncognito.com`.  

---

### Installation

#### HACS (custom repository)

1. In Home Assistant, open **HACS > Integrations**.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add `https://github.com/Rishi8078/Appwash-homeassistant` with the category **Integration**.
4. Install **AppWash** and restart Home Assistant.

#### Manual

1. Clone the repository:
   ```bash
   git clone https://github.com/Rishi8078/Appwash-homeassistant.git
   ```
2. Copy the `custom_components/appwash` folder into your Home Assistant
   `config/custom_components/` directory, so that
   `config/custom_components/appwash/manifest.json` exists.
3. Restart Home Assistant.

#### Add the integration

- Navigate to **Settings > Devices & Services**.
- Click **Add Integration** and search for "AppWash".
- Enter your AppWash account credentials when prompted.

---

### Configuration  

Credentials are entered in the config flow and stored in the config entry; nothing
needs to be placed in YAML. The location polled by the integration is taken from
your account's preferred location. To poll a different one, open the integration's
**Configure** dialog and enter a location ID.

Example dashboard card:

```yaml  
type: custom:mushroom-template-card
primary: Washing Machine
secondary: |
  {% if is_state('sensor.washing_machine_46084', 'FREE') %}
    Available
  {% elif is_state('sensor.washing_machine_46084', 'YOUR_CYCLE') %}
    Your wash ({{ state_attr('sensor.washing_machine_46084', 'remaining_minutes') }} min left)
  {% elif is_state('sensor.washing_machine_46084', 'OCCUPIED') %}
    In use by someone else
  {% else %}
    Unknown
  {% endif %}
icon: mdi:washing-machine
icon_color: |
  {% if is_state('sensor.washing_machine_46084', 'FREE') %}
    green
  {% elif is_state('sensor.washing_machine_46084', 'YOUR_CYCLE') %}
    blue
  {% elif is_state('sensor.washing_machine_46084', 'OCCUPIED') %}
    red
  {% else %}
    grey
  {% endif %}
```  

---

### Entities and attributes

| Entity | State |
| --- | --- |
| `sensor.washing_machine_<code>` | `FREE` / `OCCUPIED` / `YOUR_CYCLE` |
| `sensor.dryer_<code>` | `FREE` / `OCCUPIED` / `YOUR_CYCLE` |
| `sensor.appwash_balance` | Wallet balance in the account currency |

`YOUR_CYCLE` replaces `OCCUPIED` when the cycle running on the machine belongs
to the configured account. `availability_status` always keeps the raw API value
(`FREE` / `OCCUPIED`), so both views are available.

Machine sensors expose these attributes:

`machine_code`, `machine_name`, `machine_id`, `product_group`, `location_id`,
| Attribute | Meaning |
| --- | --- |
| `machine_code`, `machine_id` | Identity |
| `product_group` | `WM` (washer) or `TD` (tumble dryer) |
| `location_id` | Where the machine is |
| `availability_status` | Raw API value: `FREE` / `OCCUPIED` |
| `occupied_by` | `you`, `other`, or `null` when free |
| `status_since` | When the current occupancy started |
| `fulfillment_id` | Identifies the occupancy; equals your cycle id when it's yours |
| `checked_at`, `checked_from`, `checked_until` | Freshness window of the availability data |
| `cycle_price`, `currency` | Price preview for a new cycle |
| `additional_info` | The backend's occupancy sentence |
| `estimated_end`, `remaining_minutes` | Derived from the occupancy window |
| `elapsed_minutes`, `progress_percent` | Derived progress |

When one of *your* cycles is running on the machine, its details are added:

| Attribute | Meaning |
| --- | --- |
| `cycle_id`, `cycle_status` | The cycle and its state (`ENABLED`) |
| `cycle_product_type`, `cycle_product_kind` | e.g. `FIX_CYCLE_WASHING` / `CYCLE` |
| `cycle_order_id`, `cycle_termination_reason` | Order link, why it ended |
| `cycle_created_at`, `cycle_ordered_at`, `cycle_enabled_at`, `cycle_stopped_at` | Cycle timeline |
| `cycle_fulfillment_status` | `FULFILLING` while running, `FULFILLED` once done |
| `cycle_order_status`, `cycle_paid_amount`, `cycle_description` | What you were charged |

The presence of the `cycle_*` block is itself the "this one is mine" signal, so
`occupied_by` and `cycle_id` cover what a separate `is_own_cycle` flag would.

The balance sensor carries `available_balance`, `total_balance` and
`authorized_balance` as attributes.

Notify yourself when your own wash finishes:

```yaml
automation:
  - alias: My wash is done
    trigger:
      - platform: state
        entity_id: sensor.washing_machine_46084
        from: YOUR_CYCLE
        to: FREE
    action:
      - service: notify.mobile_app
        data:
          message: "Machine 46084 is done."
```

---

### How your own cycle is detected

`GET /cycles` is scoped to the authenticated account, so it only ever returns
your cycles. A busy machine carries `availability.fulfillmentId`, and for your
own cycles that value equals the cycle's `id`. The integration matches the two:

- exact match → the cycle is yours → state `YOUR_CYCLE`, `occupied_by: you`,
  and the cycle's details are added as attributes
- `fulfillmentId` set but absent from your cycles → somebody else → `OCCUPIED`,
  `occupied_by: other`
- no `fulfillmentId` → falls back to matching on machine id, which covers the
  short window after a cycle is enabled while availability still reads `FREE`

An unmatched `fulfillmentId` never falls back to the machine id, so a finished
cycle of yours cannot make a stranger's wash look like your own.

---

### How it polls

One coordinator update every 60 seconds performs exactly three read-only requests
for the whole integration, regardless of how many machines you have:

```
GET /machines?location.id=<location>
GET /cycles?page=0&size=20&location.id=<location>
GET /account/wallet
```

A fourth request, `GET /order-items?page=0&size=20&kind=CYCLE`, is added only
while one of your cycles is actually running — it supplies
`cycle_fulfillment_status` and the amount charged. With no wash of your own in
progress it is skipped entirely.

Order history (`/orders`) is available in the client but is not fetched during
normal polling.

---

### Development

```bash
pip install -r requirements_test.txt
pytest
```

The tests run against a local fake API and a local fake Cognito server; no
credentials and no network access are required.

Repository layout:

```
custom_components/appwash/   the integration (this is what HACS installs)
tests/                       test suite, no credentials or network needed
tools/                       read-only API discovery scripts, never imported
```

---

### Screenshots  
![Screenshot from 2024-11-26 00-23-57](https://github.com/user-attachments/assets/e7d5e131-9e05-4a11-bf4f-9dd2bb01f6b3)

---

### Limitations  
- Monitoring only. Starting, stopping, reserving machines or any payment operation is not implemented.  
- The API exposes no remaining-time field. `estimated_end` / `remaining_minutes` are derived from the occupancy window in `availability.additionalInfo` and are an estimate, not a live countdown.  
- Only the machine types the API reports as `WM` (washer) and `TD` (tumble dryer) get sensors.  
- Only the availability states `FREE` and `OCCUPIED` have been observed; any other value is passed through unchanged.  
- Ownership is inferred from your own cycle list. The API exposes no owner field, so a machine occupied through a route that produces no cycle for your account (a reservation, for instance) reads as `OCCUPIED`.  
- Multiple locations are not supported in a single config entry; add one entry per account and select the location in the options.  

---

### Contributing  
1. Fork the repository.  
2. Create a feature branch.  
3. Commit your changes and push the branch to your fork.  
4. Submit a pull request.  

---
