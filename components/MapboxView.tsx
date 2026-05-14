"use client";

import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import AreaRiskInspector, {
  type AreaRiskData,
} from "@/components/AreaRiskInspector";
import type { MapCityNodeData } from "@/components/MapCityNode";
import type { RegionalMappingData } from "@/components/regionalTypes";

interface MapboxViewProps {
  mapId?: string;
  cities: MapCityNodeData[];
  selectedCityName: string;
  focusedCityName: string;
  focusRequestId: number;
  areaRisk: AreaRiskData | null;
  regionalMapping: RegionalMappingData | null;
  onSelectCity: (city: MapCityNodeData) => void;
  onInspectArea: (position: { x: number; y: number }) => void;
  syncedView?: SyncedMapView | null;
  onViewChange?: (view: SyncedMapView) => void;
}

const MAPBOX_STYLE = "mapbox://styles/mapbox/dark-v11";

export interface SyncedMapView {
  center: [number, number];
  zoom: number;
  bearing: number;
  pitch: number;
  sourceId: string;
}

export default function MapboxView({
  mapId = "primary",
  cities,
  selectedCityName,
  focusedCityName,
  focusRequestId,
  areaRisk,
  regionalMapping,
  onSelectCity,
  onInspectArea,
  syncedView,
  onViewChange,
}: MapboxViewProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const regionalMarkerRef = useRef<mapboxgl.Marker | null>(null);
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
            [-13, 5],
            [88, 58],
          ],
          {
            padding: {
              top: Math.min(90, height * 0.14),
              bottom: Math.min(80, height * 0.12),
              left: Math.min(90, width * 0.12),
              right: Math.min(90, width * 0.12),
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
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_45%,transparent_0%,rgba(0,0,0,0.18)_58%,rgba(0,0,0,0.72)_100%)]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.035)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.035)_1px,transparent_1px)] [background-size:72px_72px] opacity-45"
      />

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
