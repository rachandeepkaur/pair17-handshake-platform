# JMeter result evidence

This directory contains the raw JMeter `.jtl` outputs used for the Lab 2 performance evidence. Files prefixed `aws-` targeted the EKS load-balancer endpoint; the other files targeted the local Docker gateway while validating the plan.

Completed raw runs include:

- Login: 100, 200, 300, 400, and 500 users.
- Job search: 100, 200, 300, 400, and 500 users.
- Event search: 100, 200, 300, 400, and 500 users.
- Assistant chat: 5, 10, 20, and 50 users.
- Application submission: 100 users.

The application-submission runs at 200, 300, 400, and 500 users are still required before final submission. Generated JMeter HTML reports and runtime logs are intentionally excluded because the `.jtl` files are the source data from which reports can be regenerated.
