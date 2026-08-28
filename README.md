# AppWash Home Assistant Integration  
AppWash Home Assistant Integration enables monitoring of AppWash (Miele MOVE) laundry machines from Home Assistant.  
![Python versions](https://img.shields.io/pypi/pyversions/tplinkrouterc6u)

---

### Features  
- **Real-time Monitoring:** View the availability of washing machines and dryers.  
- **Machine Availability:** See which machines are `FREE` and which are `OCCUPIED`.  
- **Cycle Details:** The active cycle (id, order, product type, timestamps) is exposed as attributes on the machine it runs on.  
- **Progress Updates:** `estimated_end` and `remaining_minutes` are derived from the occupancy window reported by the API.  
- **Wallet Balance:** Your prepaid balance as a sensor.  
- **Simple Configuration:** Setup directly within Home Assistant.  

---

### ⚠️ Upgrading from 1.x

AppWash migrated to the Miele MOVE API (`https://www.miele-move.com/appwash/api/app/v1`)
with Amazon Cognito login. Version 2.0.0 follows that migration:

- Entity IDs, entity names and unique IDs are **unchanged**.
- Machine sensor states now use the values the API reports: **`FREE`** (previously
  `AVAILABLE`) and **`OCCUPIED`**. Dashboard templates comparing against
  `AVAILABLE` must be updated — see the example below.
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
  {% elif is_state('sensor.washing_machine_46084', 'OCCUPIED') %}
    Occupied ({{ state_attr('sensor.washing_machine_46084', 'remaining_minutes') }} min left)
  {% else %}
    Unknown
  {% endif %}
icon: mdi:washing-machine
icon_color: |
  {% if is_state('sensor.washing_machine_46084', 'FREE') %}
    green
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
| `sensor.washing_machine_<code>` | `FREE` / `OCCUPIED` |
| `sensor.dryer_<code>` | `FREE` / `OCCUPIED` |
| `sensor.appwash_balance` | Wallet balance in the account currency |

Machine sensors expose these attributes:

`machine_code`, `machine_name`, `machine_id`, `product_group`, `location_id`,
`availability_status`, `status_since`, `fulfillment_id`, `checked_at`,
`checked_from`, `checked_until`, `cycle_price`, `currency`, `additional_info`,
`estimated_end`, `remaining_minutes`

When a cycle is running on the machine, its details are added:

`cycle_id`, `cycle_status`, `cycle_product_type`, `cycle_product_kind`,
`cycle_order_id`, `cycle_termination_reason`, `cycle_created_at`,
`cycle_ordered_at`, `cycle_enabled_at`, `cycle_stopped_at`

---

### How it polls

One coordinator update every 60 seconds performs exactly three read-only requests
for the whole integration, regardless of how many machines you have:

```
GET /machines?location.id=<location>
GET /cycles?page=0&size=20&location.id=<location>
GET /account/wallet
```

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
- Multiple locations are not supported in a single config entry; add one entry per account and select the location in the options.  

---

### Contributing  
1. Fork the repository.  
2. Create a feature branch.  
3. Commit your changes and push the branch to your fork.  
4. Submit a pull request.  

---

### Acknowledgments  
Special thanks to the Home Assistant community for their resources and inspiration in developing this integration.  

---
