import { describe, it, expect } from "vitest";
import { parseCSV, computeStats, getDistrictId, getDistrictLabel } from "../dataUtils";

const SAMPLE_CSV = `congressional_district_geoid,state_fips,snap_population,snap_under_18,snap_over_65,snap_employed,household_weight,median_household_income,total_weighted_snap,one_sum_test,pct_under_18,pct_over_65,employment_rate
101,1,113742.24,18612.51,35185.68,48968.76,256744.45,22425.08,271827136.11,54495.56,16.4,30.9,43.1
102,1,129165.95,23541.81,40841.78,55851.93,254964.97,21703.31,316396255.34,62587.19,18.2,31.6,43.2`;

describe("parseCSV", () => {
  it("parses CSV rows into a district data map keyed by geoid", () => {
    const result = parseCSV(SAMPLE_CSV);
    expect(Object.keys(result)).toHaveLength(2);
    expect(result[101]).toBeDefined();
    expect(result[102]).toBeDefined();
  });

  it("correctly extracts benefits in millions", () => {
    const result = parseCSV(SAMPLE_CSV);
    expect(result[101].benefits).toBeCloseTo(271.827, 1);
  });

  it("maps state FIPS to state name", () => {
    const result = parseCSV(SAMPLE_CSV);
    expect(result[101].stateName).toBe("Alabama");
  });

  it("extracts demographic percentages", () => {
    const result = parseCSV(SAMPLE_CSV);
    expect(result[101].pctUnder18).toBeCloseTo(16.4);
    expect(result[101].pctOver65).toBeCloseTo(30.9);
    expect(result[101].employmentRate).toBeCloseTo(43.1);
  });
});

describe("computeStats", () => {
  it("computes aggregate statistics from data map", () => {
    const dataMap = parseCSV(SAMPLE_CSV);
    const stats = computeStats(dataMap);
    expect(stats.districtCount).toBe(2);
    expect(stats.totalPopulation).toBeCloseTo(113742.24 + 129165.95, 0);
    expect(stats.totalBenefits).toBeCloseTo(271827136.11 + 316396255.34, -2);
  });
});

describe("getDistrictId", () => {
  it("returns cd_id for hex features", () => {
    const feature = { properties: { cd_id: 101 } };
    expect(getDistrictId(feature, "hex")).toBe(101);
  });

  it("converts STATEFP+CD118FP to integer for real features", () => {
    const feature = { properties: { STATEFP: "01", CD118FP: "01" } };
    expect(getDistrictId(feature, "real")).toBe(101);
  });

  it("converts at-large districts (00) to 01", () => {
    const feature = { properties: { STATEFP: "02", CD118FP: "00" } };
    expect(getDistrictId(feature, "real")).toBe(201);
  });
});

describe("getDistrictLabel", () => {
  it("produces a label for hex features", () => {
    const feature = {
      properties: { CDLABEL: "1", STATENAME: "Alabama", cd_id: 101 },
    };
    const snapInfo = { stateName: "Alabama" };
    const label = getDistrictLabel(feature, "hex", snapInfo);
    expect(label).toContain("Alabama");
    expect(label).toContain("1");
  });

  it("produces a label for real features", () => {
    const feature = {
      properties: {
        STATEFP: "01",
        CD118FP: "01",
        NAMELSAD: "Congressional District 1",
      },
    };
    const snapInfo = { stateName: "Alabama" };
    const label = getDistrictLabel(feature, "real", snapInfo);
    expect(label).toContain("Alabama");
    expect(label).toContain("Congressional District 1");
  });
});
