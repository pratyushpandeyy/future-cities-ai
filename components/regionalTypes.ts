export interface RegionalMappingData {
  inputLocation: string;
  mappedRegion: string;
  climateZone: string;
  confidence: "Medium" | "High";
  nearestGridCell: string;
  longitude: number;
  latitude: number;
}
