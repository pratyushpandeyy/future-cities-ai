export interface RegionalMappingData {
  inputLocation: string;
  mappedRegion: string;
  climateZone: string;
  confidence: "Medium" | "High";
  nearestGridCell: string;
  boundarySource: "simulated" | "real_geojson" | "simulated_fallback";
  longitude: number;
  latitude: number;
  locality?: string | null;
  district?: string | null;
  city?: string | null;
  country?: string | null;
  hierarchyLabel?: string | null;
  placeType?: string | null;
}
