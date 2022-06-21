# Grafana Loki label best practices

## Static labels are good

Things like, host, application, and environment are great labels. They will be fixed for a given system/app and have bounded values. Use static labels to make it easier to query your logs in a logical sense (e.g. show me all the logs for a given application and specific environment, or show me all the logs for all the apps on a specific host).

## Use dynamic labels sparingly

Too many label value combinations leads to too many streams. The penalties for that in Loki are a large index and small chunks in the store, which in turn can actually reduce performance.

## Label values must always be bounded

If you are dynamically setting labels, never use a label which can have unbounded or infinite values. This will always result in big problems for Loki.

Try to keep values bounded to as small a set as possible. We don’t have perfect guidance as to what Loki can handle, but think single digits, or maybe 10’s of values for a dynamic label. This is less critical for static labels. For example, if you have 1,000 hosts in your environment it’s going to be just fine to have a host label with 1,000 values.

## Be aware of dynamic labels applied by clients

Loki has several client options: Promtail (which also supports systemd journal ingestion and TCP-based syslog ingestion), Fluentd, Fluent Bit, a Docker plugin, and more!

# Best practices for creating dashboards

## A dashboard should tell a story or answer a question

What story are you trying to tell with your dashboard? Try to create a logical progression of data, such as large to small or general to specific. What is the goal for this dashboard? (Hint: If the dashboard doesn’t have a goal, then ask yourself if

## Dashboards should reduce cognitive load, not add to it

Dashboards should reduce cognitive load, not add to it
Cognitive load is basically how hard you need to think about something in order to figure it out. Make your dashboard easy to interpret. Other users and future you (when you’re trying to figure out what broke at 2AM) will appreciate it.

## Have a monitoring strategy

It’s easy to make new dashboards. It’s harder to optimize dashboard creation and adhere to a plan, but it’s worth it. This strategy should govern both your overall dashboard scheme and enforce consistency in individual dashboard design.
