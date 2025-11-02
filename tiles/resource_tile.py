# tiles/resource_tile.py
import time
import psutil
import streamlit as st
import os

def _sample_net(interval=0.5):
    s1 = psutil.net_io_counters()
    time.sleep(interval)
    s2 = psutil.net_io_counters()
    sent_bps = (s2.bytes_sent - s1.bytes_sent) / interval
    recv_bps = (s2.bytes_recv - s1.bytes_recv) / interval
    return sent_bps, recv_bps

def human_bytes(bps):
    units = ["B/s","KB/s","MB/s","GB/s"]
    v = float(bps)
    idx = 0
    while v >= 1024 and idx < len(units)-1:
        v /= 1024.0
        idx += 1
    return f"{v:0.2f} {units[idx]}"

def render(services, st, state):
    try:
        st.subheader("System Resource Monitor")
        cols = st.columns([3,2,2,2])

        # CPU
        cpu_pct = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count(logical=True)
        cols[0].metric("CPU Usage", f"{cpu_pct:.0f}%", delta=f"{cpu_count} cores")

        # RAM
        vm = psutil.virtual_memory()
        ram_pct = vm.percent
        cols[1].metric("RAM Usage", f"{ram_pct:.0f}%", delta=f"{vm.total//(1024**2)} MB total")

        # Disk
        du = psutil.disk_usage("/")
        disk_pct = du.percent
        cols[2].metric("Disk Used", f"{disk_pct:.0f}%", delta=f"{du.free//(1024**2)} MB free")

        # Load avg and temp
        try:
            la1, la5, la15 = psutil.getloadavg()
            load_txt = f"{la1:.2f}, {la5:.2f}, {la15:.2f}"
        except Exception:
            load_txt = "n/a"
        temp_txt = "n/a"
        try:
            rc, out, err = services.run_cmd("vcgencmd measure_temp", timeout=1) if hasattr(services, "run_cmd") else (1, None, None)
            if rc == 0 and out:
                temp_txt = out.replace("temp=","").strip()
        except Exception:
            pass
        cols[3].metric("Load 1m/5m/15m", load_txt, delta=temp_txt)

        st.markdown("### Network Bandwidth (instant sample)")
        net_sent, net_recv = _sample_net(interval=0.5)
        net_cols = st.columns(2)
        net_cols[0].metric("Upload", human_bytes(net_sent))
        net_cols[1].metric("Download", human_bytes(net_recv))

        st.markdown("### Top processes (by CPU)")
        try:
            procs = sorted(psutil.process_iter(["pid","name","cpu_percent","memory_percent"]), key=lambda p: p.info.get("cpu_percent",0), reverse=True)[:8]
            table = []
            for p in procs:
                info = p.info
                table.append({
                    "pid": info.get("pid"),
                    "name": info.get("name"),
                    "cpu%": f"{info.get('cpu_percent',0):.1f}",
                    "mem%": f"{info.get('memory_percent',0):.1f}"
                })
            st.table(table)
        except Exception as e:
            st.error(f"Failed to list processes: {e}")

        st.caption("Metrics sampled locally. If data is stale, check Pi connectivity or permissions.")
    except Exception as e:
        st.error(f"resource_tile failed: {e}")
