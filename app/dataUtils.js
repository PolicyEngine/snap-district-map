const STATE_NAMES = {
  1: "Alabama",
  2: "Alaska",
  4: "Arizona",
  5: "Arkansas",
  6: "California",
  8: "Colorado",
  9: "Connecticut",
  10: "Delaware",
  11: "District of Columbia",
  12: "Florida",
  13: "Georgia",
  15: "Hawaii",
  16: "Idaho",
  17: "Illinois",
  18: "Indiana",
  19: "Iowa",
  20: "Kansas",
  21: "Kentucky",
  22: "Louisiana",
  23: "Maine",
  24: "Maryland",
  25: "Massachusetts",
  26: "Michigan",
  27: "Minnesota",
  28: "Mississippi",
  29: "Missouri",
  30: "Montana",
  31: "Nebraska",
  32: "Nevada",
  33: "New Hampshire",
  34: "New Jersey",
  35: "New Mexico",
  36: "New York",
  37: "North Carolina",
  38: "North Dakota",
  39: "Ohio",
  40: "Oklahoma",
  41: "Oregon",
  42: "Pennsylvania",
  44: "Rhode Island",
  45: "South Carolina",
  46: "South Dakota",
  47: "Tennessee",
  48: "Texas",
  49: "Utah",
  50: "Vermont",
  51: "Virginia",
  53: "Washington",
  54: "West Virginia",
  55: "Wisconsin",
  56: "Wyoming",
};

export function parseCSV(csvText) {
  const lines = csvText.trim().split("\n");
  const dataMap = {};

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const values = line.split(",");
    const geoid = parseInt(values[0]);
    const stateFips = parseInt(values[1]);
    const benefits = parseFloat(values[8]) / 1e6;
    const population = parseFloat(values[2]);
    const pctUnder18 = parseFloat(values[10]);
    const pctOver65 = parseFloat(values[11]);
    const medianIncome = parseFloat(values[7]);
    const employmentRate = parseFloat(values[12]);

    dataMap[geoid] = {
      geoid,
      stateFips,
      stateName: STATE_NAMES[stateFips] || "Unknown",
      benefits,
      population,
      pctUnder18,
      pctOver65,
      medianIncome,
      employmentRate,
    };
  }

  return dataMap;
}

export function computeStats(dataMap) {
  const entries = Object.values(dataMap);
  const totalBenefits = entries.reduce((sum, d) => sum + d.benefits * 1e6, 0);
  const totalPopulation = entries.reduce((sum, d) => sum + (d.population || 0), 0);
  const districtCount = entries.length;
  const avgPopulation = totalPopulation / districtCount;

  return { totalBenefits, totalPopulation, districtCount, avgPopulation };
}

export function getDistrictId(feature, mapType) {
  const props = feature?.properties || {};
  // Detect by available properties, not mapType: react-simple-maps can briefly
  // render with the previous geographies array while mapType has already flipped
  // (state-update race when toggling hex <-> real). Branching on mapType then
  // crashes because the wrong key set is present.
  if (props.cd_id !== undefined && props.cd_id !== null) {
    return props.cd_id;
  }
  if (props.STATEFP && props.CD118FP) {
    const state = String(props.STATEFP).padStart(2, "0");
    const cd = String(props.CD118FP).padStart(2, "0");
    const locId = state + cd;
    let geoidInt = parseInt(locId);
    if (cd === "00") {
      geoidInt = parseInt(state) * 100 + 1;
    }
    return geoidInt;
  }
  return null;
}

export function getDistrictLabel(feature, mapType, snapInfo) {
  const props = feature?.properties || {};
  // Detect by properties (see getDistrictId rationale).
  if (props.cd_id !== undefined && props.cd_id !== null) {
    const stateName = snapInfo?.stateName || props.STATENAME || "Unknown";
    const districtLabel = props.CDLABEL || props.cd_id;
    return `${stateName} District ${districtLabel}`;
  }
  if (props.STATEFP) {
    const districtName =
      props.NAMELSAD || `District ${props.CD118FP || ""}`.trim();
    const stateFips = parseInt(props.STATEFP);
    const stateName = snapInfo?.stateName || STATE_NAMES[stateFips] || "Unknown";
    return `${stateName} - ${districtName}`;
  }
  return "Unknown";
}

export { STATE_NAMES };
