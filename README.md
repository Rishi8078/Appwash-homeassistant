### AppWash Home Assistant Integration  

AppWash Home Assistant Integration enables seamless monitoring and control of AppWash laundry devices through the Home Assistant platform. This project bridges the gap between AppWash's proprietary system and the open-source Home Assistant ecosystem, offering users a streamlined solution for smart appliance management.  

---

### Features  
- **Real-time Monitoring:** View the status of washing machines and dryers in real-time.  
- **Machine Availability:** Check which machines are free or in use.  
- **Progress Updates:** Track the remaining time of ongoing cycles.  
- **Simple Configuration:** Intuitive setup directly within Home Assistant.  

---

### Prerequisites  
Before installing this integration, ensure you have the following:  
- A working Home Assistant instance.  
- Valid AppWash account credentials.  
- Internet connectivity to communicate with AppWash's API.  

---

### Installation  

Follow these steps to install and configure the AppWash Home Assistant Integration:  

1. **Clone the Repository**  
   Clone the repository to your local system:  
   ```bash  
   git clone https://github.com/Rishi8078/Appwash-homeassistant.git  
   ```  

2. **Copy Files**  
   Place the `appwash` folder in your Home Assistant's `config/custom_components/` directory.  

3. **Restart Home Assistant**  
   Restart your Home Assistant instance to load the new integration.  

4. **Add the Integration**  
   In the Home Assistant UI:  
   - Navigate to **Settings > Integrations**.  
   - Click **Add Integration** and search for "AppWash."  
   - Enter your AppWash account credentials when prompted.  

---

### Configuration  
After installation, you may configure the integration in the Home Assistant UI. If additional YAML configuration is required, follow the example below:  

```yaml  
type: custom:mushroom-template-card
primary: Washing Machine
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
```  

---

### Screenshots  
*Add screenshots or GIFs of the integration in action here to help users visualize the features.*  
![Screenshot from 2024-11-26 00-23-57](https://github.com/user-attachments/assets/e7d5e131-9e05-4a11-bf4f-9dd2bb01f6b3)

---

### Limitations  
- Currently supports only monitoring and status updates. Control features (e.g., starting a machine) are not yet implemented.  
- Compatibility with specific AppWash devices may vary.  

---

### Contributing  
We welcome contributions to this project! If you want to contribute:  
1. Fork the repository.  
2. Create a feature branch:  
   ```bash  
   git checkout -b feature-name  
   ```  
3. Commit your changes and push the branch to your fork.  
4. Submit a pull request to this repository.  

---

### Acknowledgments  
Special thanks to the Home Assistant community for their resources and inspiration in developing this integration.  

---

Let me know if you'd like to add any visuals or links to this draft!
