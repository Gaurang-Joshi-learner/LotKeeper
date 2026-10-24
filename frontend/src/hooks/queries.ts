import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useToast } from "../components/Toasts";
import { api } from "../lib/api";
import { vehicleTitle } from "../lib/format";
import type { Filters, Hold, Vehicle, VehicleInput } from "../lib/types";

export const useAllVehicles = () => useQuery({ queryKey: ["vehicles", "all"], queryFn: api.allVehicles });

export const useSearch = (f: Filters) =>
  useQuery({ queryKey: ["vehicles", "search", f], queryFn: () => api.searchVehicles(f), placeholderData: keepPreviousData });

export const useHolds = () => useQuery({ queryKey: ["holds"], queryFn: api.myHolds, refetchInterval: 30_000 });
export const useOrders = () => useQuery({ queryKey: ["orders"], queryFn: api.myOrders });
export const useEvents = () => useQuery({ queryKey: ["events"], queryFn: api.events, refetchInterval: 5_000 });
export const useAnalytics = () => useQuery({ queryKey: ["analytics"], queryFn: api.analytics, refetchInterval: 15_000 });

const errText = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");

/** Purchase with an optimistic UI: the card updates instantly and rolls back if the server says no. */
export function usePurchase() {
  const qc = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: (v: Vehicle) => api.purchase(v.id),
    onMutate: async (v) => {
      await qc.cancelQueries({ queryKey: ["vehicles"] });
      const previousVehicles = qc.getQueriesData<Vehicle[]>({ queryKey: ["vehicles"] });
      const previousHolds = qc.getQueryData<Hold[]>(["holds"]);
      const usedHold = !!previousHolds?.some((h) => h.vehicle_id === v.id);
      qc.setQueriesData<Vehicle[]>({ queryKey: ["vehicles"] }, (old) =>
        old?.map((x) =>
          x.id !== v.id
            ? x
            : {
                ...x,
                quantity: x.quantity - 1,
                reserved: usedHold ? x.reserved - 1 : x.reserved,
                available: usedHold ? x.available : x.available - 1,
              },
        ),
      );
      if (usedHold) qc.setQueryData<Hold[]>(["holds"], previousHolds!.filter((h) => h.vehicle_id !== v.id));
      return { previousVehicles, previousHolds };
    },
    onError: (e, _v, ctx) => {
      ctx?.previousVehicles.forEach(([key, data]) => qc.setQueryData(key, data));
      qc.setQueryData(["holds"], ctx?.previousHolds);
      toast(errText(e), "error");
    },
    onSuccess: (v) => toast(`Purchased ${vehicleTitle(v)}. ${v.quantity} left on the lot.`),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["vehicles"] });
      qc.invalidateQueries({ queryKey: ["holds"] });
      qc.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}

export function useHoldActions() {
  const qc = useQueryClient();
  const toast = useToast();
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["vehicles"] });
    qc.invalidateQueries({ queryKey: ["holds"] });
  };
  const hold = useMutation({
    mutationFn: (v: Vehicle) => api.hold(v.id),
    onSuccess: (_h, v) => toast(`Holding ${vehicleTitle(v)} for you.`),
    onError: (e) => toast(errText(e), "error"),
    onSettled: refresh,
  });
  const release = useMutation({
    mutationFn: (v: Vehicle) => api.release(v.id),
    onSuccess: (_r, v) => toast(`Released the hold on ${vehicleTitle(v)}.`),
    onError: (e) => toast(errText(e), "error"),
    onSettled: refresh,
  });
  return { hold, release, refresh };
}

/** Admin mutations: anything that changes stock also refreshes the audit feed and analytics. */
export function useAdminActions() {
  const qc = useQueryClient();
  const toast = useToast();
  const refresh = () => ["vehicles", "events", "analytics", "holds"].forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
  const fail = (e: unknown) => toast(errText(e), "error");

  return {
    create: useMutation({
      mutationFn: (v: VehicleInput) => api.createVehicle(v),
      onSuccess: (v) => toast(`Added ${vehicleTitle(v)} to the lot.`),
      onError: fail,
      onSettled: refresh,
    }),
    update: useMutation({
      mutationFn: ({ id, data }: { id: number; data: Partial<VehicleInput> }) => api.updateVehicle(id, data),
      onSuccess: (v) => toast(`Saved changes to ${vehicleTitle(v)}.`),
      onError: fail,
      onSettled: refresh,
    }),
    remove: useMutation({
      mutationFn: (v: Vehicle) => api.deleteVehicle(v.id),
      onSuccess: (_r, v) => toast(`Deleted ${vehicleTitle(v)}.`),
      onError: fail,
      onSettled: refresh,
    }),
    restock: useMutation({
      mutationFn: ({ v, qty }: { v: Vehicle; qty: number }) => api.restock(v.id, qty),
      onSuccess: (v, { qty }) => toast(`Restocked ${vehicleTitle(v)} (+${qty}).`),
      onError: fail,
      onSettled: refresh,
    }),
  };
}
