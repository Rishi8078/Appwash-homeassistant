# AppWash Integration for Home Assistant

This integration allows you to monitor your AppWash washing machines and dryers in Home Assistant.

## Features
- Monitor washing machine availability and status
- Monitor dryer availability and status
- View account balance

## Installation
1. Download the latest release.
2. Create a folder named appwash custom_components directory of your Home Assistant installation.
3. Unpack the release in the created directory.
4. Add the integration through the HA interface (Configuration -> Integrations -> Add Integration)
5. Enter your AppWash credentials

## Available Sensors
- Washing Machine Availability
- Dryer Availability
- Account Balance

## Example Card
![Screenshot from 2024-11-26 00-23-57](https://github.com/user-attachments/assets/68b1b1f7-190c-4378-9c21-05a41a939c50)

```yaml
type: custom:stack-in-card
cards:
  - type: horizontal-stack
    cards:
      - type: markdown
        content: >
          ###### Washing
          Machines&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Current
          Balance: {{ states('sensor.appwash_balance') }} EUR
  - type: grid
    columns: 2
    square: false
    cards:
      - type: custom:mushroom-template-card
        primary: Appwash Number 41297
        secondary: |
          {% if is_state('sensor.washing_machine_41297', 'AVAILABLE') %}
            Available
          {% elif is_state('sensor.washing_machine_41297', 'OCCUPIED') %}
            Occupied
          {% else %}
            Unknown
          {% endif %}
        icon: mdi:washing-machine
        icon_color: |
          {% if is_state('sensor.washing_machine_41297', 'AVAILABLE') %}
            green
          {% elif is_state('sensor.washing_machine_41297', 'OCCUPIED') %}
            red
          {% else %}
            grey
          {% endif %}
      - type: custom:mushroom-template-card
        primary: Appwash Number 41298
        secondary: |
          {% if is_state('sensor.washing_machine_41298', 'AVAILABLE') %}
            Available
          {% elif is_state('sensor.washing_machine_41298', 'OCCUPIED') %}
            Occupied
          {% else %}
            Unknown
          {% endif %}
        icon: mdi:washing-machine
        icon_color: |
          {% if is_state('sensor.washing_machine_41298', 'AVAILABLE') %}
            green
          {% elif is_state('sensor.washing_machine_41298', 'OCCUPIED') %}
            red
          {% else %}
            grey
          {% endif %}
      - type: custom:mushroom-template-card
        primary: Appwash Number 41299
        secondary: |
          {% if is_state('sensor.washing_machine_41299', 'AVAILABLE') %}
            Available
          {% elif is_state('sensor.washing_machine_41299', 'OCCUPIED') %}
            Occupied
          {% else %}
            Unknown
          {% endif %}
        icon: mdi:washing-machine
        icon_color: |
          {% if is_state('sensor.washing_machine_41299', 'AVAILABLE') %}
            green
          {% elif is_state('sensor.washing_machine_41299', 'OCCUPIED') %}
            red
          {% else %}
            grey
          {% endif %}
      - type: custom:mushroom-template-card
        primary: Appwash Number 41300
        secondary: |
          {% if is_state('sensor.washing_machine_41300', 'AVAILABLE') %}
            Available
          {% elif is_state('sensor.washing_machine_41300', 'OCCUPIED') %}
            Occupied
          {% else %}
            Unknown
          {% endif %}
        icon: mdi:washing-machine
        icon_color: |
          {% if is_state('sensor.washing_machine_41300', 'AVAILABLE') %}
            green
          {% elif is_state('sensor.washing_machine_41300', 'OCCUPIED') %}
            red
          {% else %}
            grey
          {% endif %}
  - type: markdown
    content: |
      ###### Dryers
  - type: grid
    columns: 2
    square: false
    cards:
      - type: custom:mushroom-template-card
        primary: Dryer Number 41295
        secondary: |
          {% if is_state('sensor.dryer_41295', 'AVAILABLE') %}
            Available
          {% elif is_state('sensor.dryer_41295', 'OCCUPIED') %}
            Occupied
          {% else %}
            Unknown
          {% endif %}
        icon: mdi:tumble-dryer
        icon_color: |
          {% if is_state('sensor.dryer_41295', 'AVAILABLE') %}
            green
          {% elif is_state('sensor.dryer_41295', 'OCCUPIED') %}
            red
          {% else %}
            grey
          {% endif %}
      - type: custom:mushroom-template-card
        primary: Dryer Number 41296
        secondary: |
          {% if is_state('sensor.dryer_41296', 'AVAILABLE') %}
            Available
          {% elif is_state('sensor.dryer_41296', 'OCCUPIED') %}
            Occupied
          {% else %}
            Unknown
          {% endif %}
        icon: mdi:tumble-dryer
        icon_color: |
          {% if is_state('sensor.dryer_41296', 'AVAILABLE') %}
            green
          {% elif is_state('sensor.dryer_41296', 'OCCUPIED') %}
            red
          {% else %}
            grey
          {% endif %}
