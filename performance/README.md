# JMeter performance plan

`handshake_lab2.jmx` contains the five Lab 2 workloads. It uses only standard JMeter elements and the seeded student accounts. The plan sends requests through the Docker gateway at `http://localhost:9170/api` by default.

Before an application-submission run, choose three active job IDs with no applications from the 200 seeded student accounts. Pass the first ID as `-Japplication_job_base=<id>`; the plan uses that ID and the next two for 500 users. This avoids expected duplicate-application conflicts from the demo seed being counted as performance errors.

Run one CRUD scenario at each required level:

```bash
jmeter -n -t performance/handshake_lab2.jmx -Jscenario=login -Jcrud_users=100 -l performance/results/login-100.jtl
jmeter -n -t performance/handshake_lab2.jmx -Jscenario=job_search -Jcrud_users=100 -l performance/results/job-search-100.jtl
jmeter -n -t performance/handshake_lab2.jmx -Jscenario=application_submit -Jcrud_users=100 -l performance/results/application-100.jtl
jmeter -n -t performance/handshake_lab2.jmx -Jscenario=event_search -Jcrud_users=100 -l performance/results/event-search-100.jtl
```

Repeat those commands with `-Jcrud_users=200`, `300`, `400`, and `500`. For the assistant, run `-Jscenario=assistant_chat -Jassistant_users=5`, then repeat at `10`, `20`, and `50` users. Set `-Jbase_host=<host> -Jbase_port=<port>` when the gateway is elsewhere.

The plan has one loop per virtual user. This keeps write tests from repeatedly submitting the same student/job pair. Filter results by sampler label: the login sampler is intentionally included in authenticated scenarios because each virtual user needs its own token.

Do not commit `.jtl`, HTML report output, screenshots, or final measurements until the platform is stable. Record CRUD average response time, throughput, and error rate; record assistant p50, p95, p99, and error rate.
