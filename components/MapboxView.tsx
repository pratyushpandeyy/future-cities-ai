"use client";

import { useEffect, useRef } from "react";
import mapboxgl, { type ExpressionSpecification } from "mapbox-gl";
import AreaRiskInspector, {
  type AreaRiskData,
} from "@/components/AreaRiskInspector";
import ClimateOverlay from "@/components/ClimateOverlay";
import type { MapCityNodeData } from "@/components/MapCityNode";
import type { RegionalMappingData } from "@/components/regionalTypes";
import {
  createRegionBoundary,
  createRegionClimateSurface,
  type ClimateOverlayRenderModel,
} from "@/lib/climateOverlaySimulation";
import type { LocalUrbanCellData } from "@/lib/localCellSimulation";

interface MapboxViewProps {
  mapId?: string;
  cities: MapCityNodeData[];
  selectedCityName: string;
  focusedCityName: string;
  focusRequestId: number;
  areaRisk: AreaRiskData | null;
  regionalMapping: RegionalMappingData | null;
  localUrbanCell: LocalUrbanCellData | null;
  climateOverlayEnabled: boolean;
  climateOverlays: ClimateOverlayRenderModel[];
  onSelectCity: (city: MapCityNodeData) => void;
  onInspectArea: (position: {
    x: number;
    y: number;
    latitude: number;
    longitude: number;
  }) => void;
  syncedView?: SyncedMapView | null;
  onViewChange?: (view: SyncedMapView) => void;
}

const MAPBOX_STYLE = "mapbox://styles/mapbox/dark-v11";
const REGION_CLIMATE_SOURCE_ID = "future-cities-region-climate-surface";
const REGION_BOUNDARY_SOURCE_ID = "future-cities-region-boundary";
const REGION_CLIMATE_LAYER_ID = "future-cities-region-climate-fill";
const REGION_BOUNDARY_LAYER_ID = "future-cities-region-boundary-line";
const LEGACY_CLIMATE_LAYER_IDS = [
  "future-cities-climate-surface-fill",
  "future-cities-climate-surface-line",
  "future-cities-climate-surface-heatmap",
];
const LEGACY_CLIMATE_SOURCE_IDS = ["future-cities-climate-surface"];

export interface SyncedMapView {
  center: [number, number];
  zoom: number;
  bearing: number;
  pitch: number;
  sourceId: string;
}

function getClimateSurfaceColor(
  kind: ClimateOverlayRenderModel["kind"],
  colorProperty: ClimateOverlayRenderModel["colorProperty"],
  intensity: number,
): ExpressionSpecification {
  const riskValue = ["*", ["get", colorProperty], intensity];

  if (kind === "flood") {
    return [
      "interpolate",
      ["linear"],
      riskValue,
      0,
      "rgba(34,211,238,0.05)",
      42,
      "rgba(34,211,238,0.26)",
      68,
      "rgba(37,99,235,0.42)",
      98,
      "rgba(88,28,135,0.56)",
    ] as ExpressionSpecification;
  }

  if (kind === "comfort") {
    return [
      "interpolate",
      ["linear"],
      riskValue,
      0,
      "rgba(239,68,68,0.28)",
      42,
      "rgba(250,204,21,0.36)",
      68,
      "rgba(20,184,166,0.42)",
      100,
      "rgba(34,197,94,0.48)",
    ] as ExpressionSpecification;
  }

  if (kind === "livability") {
    return [
      "interpolate",
      ["linear"],
      ["*", ["-", 100, ["get", "livability"]], intensity],
      0,
      "rgba(20,184,166,0.18)",
      42,
      "rgba(250,204,21,0.32)",
      68,
      "rgba(249,115,22,0.44)",
      96,
      "rgba(127,29,29,0.58)",
    ] as ExpressionSpecification;
  }

  return [
    "interpolate",
    ["linear"],
    riskValue,
    0,
    "rgba(56,189,248,0.06)",
    44,
    "rgba(250,204,21,0.28)",
    62,
    "rgba(249,115,22,0.42)",
    82,
    "rgba(220,38,38,0.54)",
    112,
    "rgba(69,10,10,0.68)",
  ] as ExpressionSpecification;
}

function ensureRegionClimateLayers(
  map: mapboxgl.Map,
  regionalMapping: RegionalMappingData,
  activeOverlay?: ClimateOverlayRenderModel,
) {
  removeLegacyClimateLayers(map);

  const climateSource = map.getSource(REGION_CLIMATE_SOURCE_ID) as
    | mapboxgl.GeoJSONSource
    | undefined;
  const boundarySource = map.getSource(REGION_BOUNDARY_SOURCE_ID) as
    | mapboxgl.GeoJSONSource
    | undefined;
  const climateSurface = createRegionClimateSurface(
    regionalMapping,
    activeOverlay,
  );
  const boundary = createRegionBoundary(regionalMapping);

  if (climateSource) {
    climateSource.setData(climateSurface);
  } else {
    map.addSource(REGION_CLIMATE_SOURCE_ID, {
      type: "geojson",
      data: climateSurface,
    });
  }

  if (boundarySource) {
    boundarySource.setData(boundary);
  } else {
    map.addSource(REGION_BOUNDARY_SOURCE_ID, {
      type: "geojson",
      data: boundary,
    });
  }

  if (!map.getLayer(REGION_CLIMATE_LAYER_ID)) {
    const firstSymbolLayerId = map
      .getStyle()
      .layers?.find((layer) => layer.type === "symbol")?.id;

    map.addLayer(
      {
        id: REGION_CLIMATE_LAYER_ID,
        type: "fill",
        source: REGION_CLIMATE_SOURCE_ID,
        layout: { visibility: "none" },
        paint: {
          "fill-antialias": true,
          "fill-color": [
            "interpolate",
            ["linear"],
            ["get", "heat"],
            0,
            "rgba(56,189,248,0.06)",
            44,
            "rgba(250,204,21,0.28)",
            62,
            "rgba(249,115,22,0.42)",
            82,
            "rgba(220,38,38,0.54)",
            112,
            "rgba(69,10,10,0.68)",
          ],
          "fill-opacity": 0,
        },
      },
      firstSymbolLayerId,
    );
  }

  if (!map.getLayer(REGION_BOUNDARY_LAYER_ID)) {
    map.addLayer({
      id: REGION_BOUNDARY_LAYER_ID,
      type: "line",
      source: REGION_BOUNDARY_SOURCE_ID,
      layout: { visibility: "none" },
      paint: {
        "line-color": "rgba(165,243,252,0.86)",
        "line-opacity": 0,
        "line-width": [
          "interpolate",
          ["linear"],
          ["zoom"],
          2,
          1,
          6,
          2.2,
        ],
        "line-blur": 0.8,
      },
    });
  }
}

function removeLegacyClimateLayers(map: mapboxgl.Map) {
  LEGACY_CLIMATE_LAYER_IDS.forEach((layerId) => {
    if (map.getLayer(layerId)) {
      map.removeLayer(layerId);
    }
  });

  LEGACY_CLIMATE_SOURCE_IDS.forEach((sourceId) => {
    if (map.getSource(sourceId)) {
      map.removeSource(sourceId);
    }
  });
}

function getClimateSurfaceOpacity(opacity: number): ExpressionSpecification {
  return [
    "*",
    opacity,
    ["coalesce", ["get", "alpha"], 0.5],
  ] as ExpressionSpecification;
}

function applyClimateSurface(
  map: mapboxgl.Map,
  climateOverlayEnabled: boolean,
  activeOverlay: ClimateOverlayRenderModel | undefined,
  regionalMapping: RegionalMappingData | null,
) {
  if (!regionalMapping) {
    removeLegacyClimateLayers(map);

    if (map.getLayer(REGION_CLIMATE_LAYER_ID)) {
      map.setLayoutProperty(REGION_CLIMATE_LAYER_ID, "visibility", "none");
      map.setPaintProperty(REGION_CLIMATE_LAYER_ID, "fill-opacity", 0);
    }

    if (map.getLayer(REGION_BOUNDARY_LAYER_ID)) {
      map.setLayoutProperty(REGION_BOUNDARY_LAYER_ID, "visibility", "none");
      map.setPaintProperty(REGION_BOUNDARY_LAYER_ID, "line-opacity", 0);
    }

    return;
  }

  ensureRegionClimateLayers(map, regionalMapping, activeOverlay);

  if (!climateOverlayEnabled || !activeOverlay) {
    map.setLayoutProperty(REGION_CLIMATE_LAYER_ID, "visibility", "none");
    map.setPaintProperty(REGION_CLIMATE_LAYER_ID, "fill-opacity", 0);
    map.setLayoutProperty(REGION_BOUNDARY_LAYER_ID, "visibility", "none");
    map.setPaintProperty(REGION_BOUNDARY_LAYER_ID, "line-opacity", 0);
    return;
  }

  map.setLayoutProperty(REGION_CLIMATE_LAYER_ID, "visibility", "visible");
  map.setPaintProperty(
    REGION_CLIMATE_LAYER_ID,
    "fill-color",
    getClimateSurfaceColor(
      activeOverlay.kind,
      activeOverlay.colorProperty,
      activeOverlay.intensity,
    ),
  );
  map.setPaintProperty(
    REGION_CLIMATE_LAYER_ID,
    "fill-opacity",
    getClimateSurfaceOpacity(activeOverlay.opacity),
  );
  map.setLayoutProperty(REGION_BOUNDARY_LAYER_ID, "visibility", "visible");
  map.setPaintProperty(REGION_BOUNDARY_LAYER_ID, "line-opacity", 0.72);
}

export default function MapboxView({
  mapId = "primary",
  cities,
  selectedCityName,
  focusedCityName,
  focusRequestId,
  areaRisk,
  regionalMapping,
  localUrbanCell,
  climateOverlayEnabled,
  climateOverlays,
  onSelectCity,
  onInspectArea,
  syncedView,
  onViewChange,
}: MapboxViewProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const regionalMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const localCellMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const hasFitInitialBoundsRef = useRef(false);
  const isApplyingSyncedViewRef = useRef(false);
  const hasMapboxToken = Boolean(process.env.NEXT_PUBLIC_MAPBOX_TOKEN);

  useEffect(() => {
    const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

    if (!mapContainerRef.current || mapRef.current || !token) {
      return;
    }

    mapboxgl.accessToken = token;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: MAPBOX_STYLE,
      center: [31, 30],
      zoom: 1.55,
      minZoom: 1.1,
      maxZoom: 8,
      projection: "globe",
    });

    map.addControl(
      new mapboxgl.NavigationControl({ showCompass: false }),
      "bottom-left",
    );

    const resizeMap = () => {
      map.resize();
    };

    const fitMapToCities = () => {
      if (!mapContainerRef.current || hasFitInitialBoundsRef.current) {
        return;
      }

      const { width, height } = mapContainerRef.current.getBoundingClientRect();

      if (width < 320 || height < 320) {
        return;
      }

      try {
        resizeMap();
        map.fitBounds(
          [
            [-18, -8],
            [105, 64],
          ],
          {
            padding: {
              top: Math.min(70, height * 0.1),
              bottom: Math.min(34, height * 0.05),
              left: Math.min(42, width * 0.055),
              right: Math.min(42, width * 0.055),
            },
            duration: 0,
          },
        );
        hasFitInitialBoundsRef.current = true;
      } catch {
        resizeMap();
      }
    };

    map.once("load", () => {
      map.setFog({
        color: "rgb(3, 8, 18)",
        "high-color": "rgb(12, 55, 72)",
        "horizon-blend": 0.08,
        "space-color": "rgb(0, 2, 8)",
        "star-intensity": 0.08,
      });
      window.requestAnimationFrame(fitMapToCities);
    });

    const resizeObserver = new ResizeObserver(() => {
      resizeMap();
      fitMapToCities();
    });
    resizeObserver.observe(mapContainerRef.current);

    const resizeTimeout = window.setTimeout(resizeMap, 450);
    const fitTimeout = window.setTimeout(fitMapToCities, 900);

    map.on("click", (event) => {
      if (!mapContainerRef.current) {
        return;
      }

      const bounds = mapContainerRef.current.getBoundingClientRect();
      const x =
        ((event.originalEvent.clientX - bounds.left) / bounds.width) * 100;
      const y =
        ((event.originalEvent.clientY - bounds.top) / bounds.height) * 100;

      onInspectArea({
        x: Math.min(100, Math.max(0, x)),
        y: Math.min(100, Math.max(0, y)),
        latitude: event.lngLat.lat,
        longitude: event.lngLat.lng,
      });
    });

    map.on("move", () => {
      if (!onViewChange || isApplyingSyncedViewRef.current) {
        return;
      }

      const center = map.getCenter();

      onViewChange({
        center: [center.lng, center.lat],
        zoom: map.getZoom(),
        bearing: map.getBearing(),
        pitch: map.getPitch(),
        sourceId: mapId,
      });
    });

    mapRef.current = map;

    return () => {
      window.clearTimeout(resizeTimeout);
      window.clearTimeout(fitTimeout);
      resizeObserver.disconnect();
      markersRef.current.forEach((marker) => marker.remove());
      markersRef.current = [];
      regionalMarkerRef.current?.remove();
      regionalMarkerRef.current = null;
      localCellMarkerRef.current?.remove();
      localCellMarkerRef.current = null;
      map.remove();
      mapRef.current = null;
      hasFitInitialBoundsRef.current = false;
    };
  }, [mapId, onInspectArea, onViewChange]);

  useEffect(() => {
    const map = mapRef.current;

    if (!map) {
      return;
    }

    const updateClimateSurface = () => {
      applyClimateSurface(
        map,
        climateOverlayEnabled,
        climateOverlays[0],
        regionalMapping,
      );
    };

    if (map.loaded()) {
      updateClimateSurface();
    } else {
      map.once("load", updateClimateSurface);
    }
  }, [climateOverlayEnabled, climateOverlays, regionalMapping]);

  useEffect(() => {
    const map = mapRef.current;

    if (!map) {
      return;
    }

    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = cities.map((city) => {
      const markerElement = document.createElement("button");
      markerElement.type = "button";
      markerElement.setAttribute(
        "aria-label",
        `Open intelligence for ${city.name}`,
      );
      markerElement.className = "future-city-marker";
      markerElement.dataset.selected = String(city.name === selectedCityName);

      const glowElement = document.createElement("span");
      glowElement.className = "future-city-marker__glow";

      const pulseElement = document.createElement("span");
      pulseElement.className = "future-city-marker__pulse";

      const coreElement = document.createElement("span");
      coreElement.className = "future-city-marker__core";

      const labelElement = document.createElement("span");
      labelElement.className = "future-city-marker__label";
      labelElement.textContent = city.name;

      markerElement.append(glowElement, pulseElement, coreElement, labelElement);
      markerElement.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        onSelectCity(city);
        map.flyTo({
          center: [city.longitude, city.latitude],
          zoom: Math.max(map.getZoom(), 3.2),
          duration: 900,
          essential: true,
        });
      });

      return new mapboxgl.Marker({
        element: markerElement,
        anchor: "center",
      })
        .setLngLat([city.longitude, city.latitude])
        .addTo(map);
    });
  }, [cities, onSelectCity, selectedCityName]);

  useEffect(() => {
    const map = mapRef.current;

    if (!map) {
      return;
    }

    regionalMarkerRef.current?.remove();
    regionalMarkerRef.current = null;

    if (!regionalMapping) {
      return;
    }

    const markerElement = document.createElement("div");
    markerElement.className = "future-region-marker";

    const glowElement = document.createElement("span");
    glowElement.className = "future-region-marker__glow";

    const pulseElement = document.createElement("span");
    pulseElement.className = "future-region-marker__pulse";

    const coreElement = document.createElement("span");
    coreElement.className = "future-region-marker__core";

    const labelElement = document.createElement("span");
    labelElement.className = "future-region-marker__label";
    labelElement.textContent = regionalMapping.inputLocation;

    markerElement.append(glowElement, pulseElement, coreElement, labelElement);

    regionalMarkerRef.current = new mapboxgl.Marker({
      element: markerElement,
      anchor: "center",
    })
      .setLngLat([regionalMapping.longitude, regionalMapping.latitude])
      .addTo(map);

    map.flyTo({
      center: [regionalMapping.longitude, regionalMapping.latitude],
      zoom: Math.max(map.getZoom(), 4),
      duration: 900,
      essential: true,
    });
  }, [regionalMapping]);

  useEffect(() => {
    const map = mapRef.current;

    if (!map) {
      return;
    }

    localCellMarkerRef.current?.remove();
    localCellMarkerRef.current = null;

    if (!localUrbanCell) {
      return;
    }

    const markerElement = document.createElement("div");
    markerElement.className = "future-local-cell-marker";

    const haloElement = document.createElement("span");
    haloElement.className = "future-local-cell-marker__halo";

    const coreElement = document.createElement("span");
    coreElement.className = "future-local-cell-marker__core";

    markerElement.append(haloElement, coreElement);

    localCellMarkerRef.current = new mapboxgl.Marker({
      element: markerElement,
      anchor: "center",
    })
      .setLngLat([localUrbanCell.longitude, localUrbanCell.latitude])
      .addTo(map);
  }, [localUrbanCell]);

  useEffect(() => {
    const map = mapRef.current;
    const city = cities.find(
      (currentCity) => currentCity.name === focusedCityName,
    );

    if (!map || !city || focusRequestId === 0) {
      return;
    }

    map.flyTo({
      center: [city.longitude, city.latitude],
      zoom: Math.max(map.getZoom(), 4),
      duration: 900,
      essential: true,
    });
  }, [cities, focusedCityName, focusRequestId]);

  useEffect(() => {
    const map = mapRef.current;

    if (!map || !syncedView || syncedView.sourceId === mapId) {
      return;
    }

    isApplyingSyncedViewRef.current = true;
    map.jumpTo({
      center: syncedView.center,
      zoom: syncedView.zoom,
      bearing: syncedView.bearing,
      pitch: syncedView.pitch,
    });

    window.requestAnimationFrame(() => {
      isApplyingSyncedViewRef.current = false;
    });
  }, [mapId, syncedView]);

  return (
    <div className="relative h-full w-full overflow-hidden bg-slate-950">
      <div ref={mapContainerRef} className="absolute inset-0 h-full w-full" />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-20 bg-[radial-gradient(circle_at_50%_45%,transparent_0%,rgba(0,0,0,0.18)_58%,rgba(0,0,0,0.72)_100%)]"
      />
      <ClimateOverlay
        enabled={climateOverlayEnabled && Boolean(regionalMapping)}
        overlays={climateOverlays}
        regionLabel={regionalMapping?.mappedRegion}
      />
      {climateOverlayEnabled && !regionalMapping ? (
        <div className="pointer-events-none absolute bottom-24 right-4 z-30 w-64 rounded-lg border border-cyan-100/15 bg-black/60 p-3 text-sm leading-5 text-cyan-50/70 shadow-[0_18px_60px_rgba(0,0,0,0.45)] backdrop-blur-2xl">
          Search a place to view regional climate overlay.
        </div>
      ) : null}

      {!hasMapboxToken ? (
        <div className="absolute inset-0 z-40 flex items-center justify-center bg-black/70 p-6 text-center backdrop-blur-xl">
          <div className="max-w-sm rounded-lg border border-white/10 bg-white/[0.055] p-5 shadow-2xl">
            <p className="text-sm font-medium text-white">Mapbox token missing</p>
            <p className="mt-2 text-sm leading-6 text-white/55">
              Add NEXT_PUBLIC_MAPBOX_TOKEN to your local environment to load the
              live dark map.
            </p>
          </div>
        </div>
      ) : null}

      {areaRisk ? <AreaRiskInspector area={areaRisk} /> : null}
    </div>
  );
}
