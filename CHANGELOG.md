# Change Log

## [2.5.5](https://github.com/IBM/kubernetes-driver/tree/2.5.5) (2025-04-08)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.5.4...2.5.5)

- Uplift Helm to version 3.16.4 (fixes CVE-2024-45337)
- Switch use of flags to enable/disable SSL to ensure SSL is enabled by default and to remove failing if statement

## [2.5.4](https://github.com/IBM/kubernetes-driver/tree/2.5.4) (2024-11-11)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.5.3...2.5.4)

- Rebuild to pick up security patches for CVE-2024-45490, CVE-2024-45491 and CVE-2024-45492

## [2.5.3](https://github.com/IBM/kubernetes-driver/tree/2.5.3) (2024-07-18)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.5.2...2.5.3)

- Update Ignition to 3.6.3 to fix the issue of request transfer-encoding with chunked format
- Update Helm to v3.15.0 for fixing security vulnerability - CVE-2023-45288

## [2.5.2](https://github.com/IBM/kubernetes-driver/tree/2.5.2) (2024-06-17)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.5.1...2.5.2)

- Update ignition version to 3.6.2 to fix for CP4NA UI driver log messages issue with ansible-lifecycle-driver

## [2.5.1](https://github.com/IBM/kubernetes-driver/tree/2.5.1) (2024-05-29)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.5.0...2.5.1)

- Update ignition version to 3.6.1 [\#208](https://github.com/IBM/kubernetes-driver/issues/208)
- Uplift helm version to fix vulnerability CVE-2024-24557 [\#206](https://github.com/IBM/kubernetes-driver/issues/206)
- Security vulnerability CVE-2024-1135 [\#204](https://github.com/IBM/kubernetes-driver/issues/204)

## [2.5.0](https://github.com/IBM/kubernetes-driver/tree/2.5.0) (2024-04-19)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.4.4...2.5.0)

- Updated Ignition to 3.6.0 that uses connexion 3.0.5 (ASGI) [\#199](https://github.com/IBM/kubernetes-driver/issues/199)

## [2.4.4](https://github.com/IBM/kubernetes-driver/tree/2.4.4) (2024-03-15)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.4.3...2.4.4)

- helm charts fails to run with kubedriver by default [\#195](https://github.com/IBM/kubernetes-driver/issues/195)

## [2.4.3](https://github.com/IBM/kubernetes-driver/tree/2.4.3) (2024-01-18)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.4.2...2.4.3)

- Fix security vulnerabilities [\#191](https://github.com/IBM/kubernetes-driver/issues/191)

## [2.4.2](https://github.com/IBM/kubernetes-driver/tree/2.4.2) (2023-11-29)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.4.1...2.4.2)

- Update helm to 3.13.2 to fix Vulnerabilitie [\#186](https://github.com/IBM/kubernetes-driver/issues/186)

## [2.4.1](https://github.com/IBM/kubernetes-driver/tree/2.4.1) (2023-09-20)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.4.0...2.4.1)

- Update helm to 3.12.3 to fix Vulnerabilitie [\#180](https://github.com/IBM/kubernetes-driver/issues/180)

## [2.4.0](https://github.com/IBM/kubernetes-driver/tree/2.4.0) (2023-07-27)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.4.0-rc2...2.4.0)

- Build the kubernetes-driver with 'rc' tag. [\#163](https://github.com/IBM/kubernetes-driver/issues/163)
- Update helm to 3.12.1 to fix Vulnerabilities [\#165](https://github.com/IBM/kubernetes-driver/issues/165)
- Update Ignition to latest version 3.5.2 [\#170](https://github.com/IBM/kubernetes-driver/issues/170)

## [2.4.0-rc2](https://github.com/IBM/kubernetes-driver/tree/2.4.0-rc2) (2023-07-26)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.4.0-rc1...2.4.0-rc2)

- Update Ignition to latest version 3.5.2 [\#170](https://github.com/IBM/kubernetes-driver/issues/170)

## [2.4.0-rc1](https://github.com/IBM/kubernetes-driver/tree/2.4.0-rc1) (2023-07-12)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.3.0...2.4.0-rc1)

- Build the kubernetes-driver with 'rc' tag. [\#163](https://github.com/IBM/kubernetes-driver/issues/163)
- Update helm to 3.12.1 to fix Vulnerabilities [\#165](https://github.com/IBM/kubernetes-driver/issues/165)

## [2.3.0](https://github.com/IBM/kubernetes-driver/tree/2.3.0) (2023-04-20)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.2.0...2.3.0)

- Update Ignition to latest version 3.5.1. [\#154](https://github.com/IBM/kubernetes-driver/issues/154)
- Update helm to fix vulnerabilities [\#156](https://github.com/IBM/kubernetes-driver/issues/156)

## [2.2.0](https://github.com/IBM/kubernetes-driver/tree/2.2.0) (2023-04-10)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.1.3...2.2.0)

- Helm chart installs successfully but lifecycle transition fails. [\#56](https://github.com/IBM/kubernetes-driver/issues/56)
- Enhancement - External Request and Response Logs [\#143](https://github.com/IBM/kubernetes-driver/issues/143)
- Log Helm commands and responses for external calls and also resolve the name in uri value in external Kube Object APIs [\#145](https://github.com/IBM/kubernetes-driver/issues/145)
- Fix security vulnerabilities [\#148](https://github.com/IBM/kubernetes-driver/issues/148)

## [2.1.3](https://github.com/IBM/kubernetes-driver/tree/2.1.3) (2023-01-27)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.1.2...2.1.3)

- Error while using kube driver to deploy a Helm chart [\#134](https://github.com/IBM/kubernetes-driver/issues/134)

## [2.1.2](https://github.com/IBM/kubernetes-driver/tree/2.1.2) (2022-12-08)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.1.1...2.1.2)

- Fix vulnerability [\#129](https://github.com/IBM/kubernetes-driver/issues/129)
- Update ignition version to 3.4.2 [\#131](https://github.com/IBM/kubernetes-driver/issues/131)

## [2.1.1](https://github.com/IBM/kubernetes-driver/tree/2.1.1) (2022-09-29)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.1.0...2.1.1)

- Update Ignition version to latest 3.4.1 [\#122](https://github.com/IBM/kubernetes-driver/issues/122)
- Fix Vulnerabilities [\#120](https://github.com/IBM/kubernetes-driver/issues/120)
- Update Documentation of Kubernetes Driver [\#118](https://github.com/IBM/kubernetes-driver/issues/118)

## [2.1.0](https://github.com/IBM/kubernetes-driver/tree/2.1.0) (2022-09-07)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.0.2...2.1.0)

- Update Ignition version to latest 3.4.0 [\#110](https://github.com/IBM/kubernetes-driver/issues/110)
- Adding note for KAFKA address change [\#100](https://github.com/IBM/kubernetes-driver/issues/100)
- Fix Vulnerabilities [\#95](https://github.com/IBM/kubernetes-driver/issues/95)
- Enable Logging for External Request & Response [\#102](https://github.com/IBM/kubernetes-driver/issues/102)
- Update install instructions for Kubernetes Driver [\#104](https://github.com/IBM/kubernetes-driver/issues/104)

## [2.0.2](https://github.com/IBM/kubernetes-driver/tree/2.0.2) (2022-05-31)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.0.1...2.0.2)

- Fixed vulnerabilities [\#96](https://github.com/IBM/kubernetes-driver/issues/96)
- Kafka instance name changed & updated ignition version [\#94](https://github.com/IBM/kubernetes-driver/issues/94)
- Update docker image location [\#93](https://github.com/IBM/kubernetes-driver/issues/93)

## [2.0.1](https://github.com/IBM/kubernetes-driver/tree/2.0.1) (2022-03-15)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.0.0...2.0.1)

- Vulnerability fixed, swagger reference removed [\#85](https://github.com/IBM/kubernetes-driver/issues/85)
- Ingress removed [\#87](https://github.com/IBM/kubernetes-driver/issues/87)

## [2.0.0](https://github.com/IBM/kubernetes-driver/tree/2.0.0) (2022-02-11)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/1.4.0...2.0.0)

- Kubernetes Vulnerabilities Issues [\#75](https://github.com/IBM/kubernetes-driver/issues/75)
- Removed Helm2 support [\#80](https://github.com/IBM/kubernetes-driver/issues/80)

## [1.4.0](https://github.com/IBM/kubernetes-driver/tree/1.4.0) (2022-01-13)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/1.3.0...1.4.0)

- Kubernetes Vulnerabilities Issues [\#59](https://github.com/IBM/kubernetes-driver/issues/59)

## [1.3.0](https://github.com/IBM/kubernetes-driver/tree/1.3.0) (2021-12-10)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/1.2.0...1.3.0

**Implement Enhancements**

- Remove uwsgi and support graceful shutdown [\#55](https://github.com/IBM/kubernetes-driver/issues/55)

## [1.2.0](https://github.com/IBM/kubernetes-driver/tree/1.2.0) (2021-08-13)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/1.1.0...1.2.0

**Implement Enhancements**

- Uplift dependency versions [\#51](https://github.com/IBM/kubernetes-driver/issues/51)

## [1.1.0](https://github.com/IBM/kubernetes-driver/tree/1.1.0) (2021-07-16)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/1.0.1...1.1.0

**Implement Enhancements**

- Add support for multiple values file and set-file option in Helm deploy action [\#47](https://github.com/IBM/kubernetes-driver/issues/47)
- Allow name and content of readyCheck script to be templated [\#46](https://github.com/IBM/kubernetes-driver/issues/46)
- Uplift dependency versions [\#41](https://github.com/IBM/kubernetes-driver/issues/41)

**Bug Fixes:**

- immediateCleanupOn: Failure not working [\#40](https://github.com/IBM/kubernetes-driver/issues/40)

## [1.0.1](https://github.com/IBM/kubernetes-driver/tree/1.0.1) (2021-05-20)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/1.0.0...1.0.1)

**Bug Fixes:**

- Kubedriver generating invalid label names [\#35](https://github.com/IBM/kubernetes-driver/issues/35)

## [1.0.0](https://github.com/IBM/kubernetes-driver/tree/1.0.0) (2021-04-29)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/0.0.5...1.0.0)

**Implemented Enhancements:**

- Update connection_address to iaf-system-kafka-bootstrap:9092 in driver values.yaml to be compatible with TNC-O installed with IAF [\#31](https://github.com/IBM/kubernetes-driver/issues/31)

- Support structured properties [\#29](https://github.com/IBM/kubernetes-driver/issues/29)

- Check Helm release has created all objects and add wait option[\#17](https://github.com/IBM/kubernetes-driver/issues/17)

- For Helm Installs support tiller-namespace helm parameter [\#11](https://github.com/IBM/kubernetes-driver/issues/11)

Template:

## [VERSION NUMBER](https://github.com/IBM/kubernetes-driver/tree/VERSION NUMBER) (YYYY-MM-DD)

[Full Changelog](https://github.com/IBM/kubernetes-driver/compare/2.1.0)

**Fixed bugs:**

- ISSUE_TITLE [#1](https://github.com/IBM/kubernetes-driver/issues/1)

**Implemented Enhancements:**

- ISSUE_TITLE [#1](https://github.com/IBM/kubernetes-driver/issues/1)

**Doc Updates:**

- ISSUE_TITLE [#1](https://github.com/IBM/kubernetes-driver/issues/1)
