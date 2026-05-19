export interface RegionalMappingData {
  inputLocation: string;
  mappedRegion: string;
  climateZone: string;
  confidence: "Medium" | "High";
  nearestGridCell: string;
  boundarySource: "database" | "simulated" | "real_geojson" | "simulated_fallback";
  boundaryName?: string | null;
  boundaryMatchReason?: string | null;
  dbBoundaryId?: number | null;
  boundaryClimateRegionType?: string | null;
  longitude: number;
  latitude: number;
  locality?: string | null;
  district?: string | null;
  city?: string | null;
  country?: string | null;
  hierarchyLabel?: string | null;
  placeType?: string | null;
}
