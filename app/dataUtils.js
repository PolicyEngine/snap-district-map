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
  if (mapType === "hex") {
    return feature.properties.cd_id;
  }
  const state = feature.properties.STATEFP.padStart(2, "0");
  const cd = feature.properties.CD118FP.padStart(2, "0");
  const locId = state + cd;
  let geoidInt = parseInt(locId);
  if (cd === "00") {
    geoidInt = parseInt(state) * 100 + 1;
  }
  return geoidInt;
}

export function getDistrictLabel(feature, mapType, snapInfo) {
  if (mapType === "hex") {
    const stateName = snapInfo?.stateName || feature.properties.STATENAME || "Unknown";
    const districtLabel = feature.properties.CDLABEL || feature.properties.cd_id;
    return `${stateName} District ${districtLabel}`;
  }
  const districtName =
    feature.properties.NAMELSAD || `District ${feature.properties.CD118FP}`;
  const stateFips = parseInt(feature.properties.STATEFP);
  const stateName = snapInfo?.stateName || STATE_NAMES[stateFips] || "Unknown";
  return `${stateName} - ${districtName}`;
}

export { STATE_NAMES };
