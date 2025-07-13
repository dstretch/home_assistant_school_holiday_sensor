
# School Holiday Sensor for Home Assistant

This integration creates a binary sensor that is `on` during selected school holiday periods based on country and region data loaded from YAML.

## Features

- Selectable country and region
- Custom YAML holiday definitions
- Boolean sensor `binary_sensor.school_holiday` active during configured holiday periods
- Community-contributable holiday files

## How to Install

1. Go to Home Assistant → HACS → Integrations.
2. Click the three-dot menu → **Custom Repositories**.
3. Add this repository URL:
   ```
   https://github.com/bsmeding/home_assistant_school_holiday_sensor
   ```
   as an **Integration**.
4. Search for `School Holiday Sensor` in HACS and install it.
5. Restart Home Assistant.
6. Go to Settings → Devices & Services → Add Integration → Search for **School Holiday Sensor**.
7. Follow the steps to configure your country, region, and holidays.

---

## Contributing

We welcome community contributions to expand holiday data for more countries or update existing entries.

### To Add a New Country:

1. Navigate to `custom_components/school_holiday_sensor/holidays/`.
2. Create a new file named `<cc>.yaml` where `<cc>` is the ISO 2-letter country code, e.g., `de.yaml` for Germany.
3. Structure the file like this:

```yaml
# source: https://example.org/official-holiday-site
- name: Region Name
  holidays:
    - name: Holiday Name
      date_from: DD-MM-YYYY
      date_till: DD-MM-YYYY
```

### To Update Existing Holidays:

- Edit the relevant `<country>.yaml` file.
- Keep existing regions in place if possible.
- Make sure new holidays use the correct format.

> ✅ **Note**: All dates must use the format `DD-MM-YYYY` to match parsing logic in the integration.

### Submitting a Pull Request

1. Fork the repository.
2. Commit your changes to a new branch.
3. Open a pull request with a brief description and source links for the added/updated data.

Let’s build a global library of school holidays together!
