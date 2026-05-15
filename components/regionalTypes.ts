export interface RegionalMappingData {
  inputLocation: string;
  mappedRegion: string;
  climateZone: string;
  confidence: "Medium" | "High";
  nearestGridCell: string;
  boundarySource: "simulated";
  longitude: number;
  latitude: number;
}
