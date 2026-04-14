# Known Error Database

When analyzing logs from `get_recent_errors.py`, refer to this database for root cause analysis:

- **Error Code OOM-101**: Out of Memory. 
  - **Symptoms**: Memory utilization > 80%, "Memory limit exceeded" logs.
  - **Solution**: Decrease `max_concurrency` to 20 or increase memory limits.

- **Error Code T/O-202**: Downstream Timeout. 
  - **Symptoms**: High routing/pending time, "upstream request timeout" logs.
  - **Solution**: Check database locks or downstream API health.

- **Error Code CFG-303**: Bad Startup Probe. 
  - **Symptoms**: "Container failed to start" logs, zero traffic.
  - **Solution**: Verify container port binding and startup probe path.
