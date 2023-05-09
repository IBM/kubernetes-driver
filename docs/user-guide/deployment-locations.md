# Deployment Locations

A deployment location must be provided to an infrastructure request to indicate the Kubernetes environment to be used. The deployment location will be managed by the Lifecycle Manager and Brent but must have particular properties to be successfully used by this driver.

# Properties

The following properties are supported by the driver:


| Name            | Default | Required                           | Detail                                                                                                                     |
| --------------- | ------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| clientConfig      | -       | Y                                  | A multiline string version of the kubectl config file used to access the target cluster (see more details [below](#obtaining-clientconfig)) |
| defaultObjectNamespace | default | N | Sets the default namespace used when deploying Kubernetes objects on a create request. This value is only used when the object does not have a specified namespace in the metadata section of it's configuration |
| driverNamespace     | Value of defaultObjectNamepsace/default_object_namespace      | N | Sets the namespace to be used by the driver for any Kubernetes objects it creates for management purposes |
| helm.version     | 3.11.3      | N | Determines the helm client version to use when deploying helm charts (allowed values: 3.11.3) |
| helm.tls.cacert | - | N | Contents of the CA certificate (if used) |
| helm.tls.cert | - | N | Contents of the helm client certificate |
| helm.tls.key | - | N | Contents of the helm client key |

**Note:** when using Helm your target deployment location must be using a compatible server version for 3.11.3 (check with `helm version` on the server).

# Obtaining clientConfig

## Kubeadm 

The easiest way to obtain the client configuration for your Kubernetes cluster is to run the `config view` command from a machine with existing kubectl access:

```
# --raw is required to prevent omission certificate values
kubectl config view --raw
```

This will output a YAML document. If you don't have kubectl access you can obtain this document by accessing `/etc/kubernetes/admin.conf` from your Kubernetes master host:

```
sudo cat /etc/kubernetes/admin.conf
```

Copy the contents from the console (or file) into your deployment location properties as a multiline string value:

```
clientConfig: |
  apiVersion: v1
  clusters:
  - cluster:
      certificate-authority-data: <sensitive data removed from docs>
      server: https://203.0.113.254:6443
    name: kubernetes
  contexts:
  - context:
      cluster: kubernetes
      user: kubernetes-admin
    name: kubernetes-admin@kubernetes
  current-context: kubernetes-admin@kubernetes
  kind: Config
  preferences: {}
  users:
  - name: kubernetes-admin
    user:
      client-certificate-data: <sensitive data removed from docs>
```

Only use this method if you are comfortable with the user in use and the permissions they have been granted through their role bindings.

## Microk8s

For microk8s, you may try `kubectl config view` but you may notice the server address as `127.0.0.1` which is not going to work for remote connections.

Instead, try:

```
microk8s.config
```

If this commands fails with "unrecognised" but you know you have microk8s installed, make the sure your `snap` bin is on your `PATH` environment variable (usually `/snap/bin`).

# Helm TLS

You need to configure the `helm.tls` properties if you would normally add the `--tls` option when executing `helm` commands against your target environment, for example:

```
helm ls --tls
```

If you remove the `--tls` option you'll likely see `Error: transport is closing`. 

If TLS is enabled, you must add the contents of the certificate and keys to the deployment location. These files will usually be in the helm home directory (on the server you use the helm CLI from):

```
ls $(helm home)

cache  ca.pem  cert.pem  key.pem  plugins  repository  starters
```

The files may have different names and you may not have a CA file (`ca.pem`). 

If you normally provide custom paths with the `--tls-ca-cert`, `--tls-cert` and `--tls-key` options then use those files instead.

Once you've identified the certificate and key files used by your helm CLI, obtain their contents by printing to the console (or open in a text editor):

```
cat $(helm home)/cert.pem
```

Copy the contents from the console (or file) into your deployment location properties as a multiline string value:

```
helm.tls.cert: |
  -----BEGIN CERTIFICATE-----
  MIIFWjCCA0ICCQD5Avb/OJ3QcTANBgkqhkiG9w0BAQsFADB6MQswCQYDVQQGEwJV
  SzETMBEGA1UECAwKU29tZS1TdGF0ZTEQMA4GA1UECgwHQWNjYW50bzEQMA4GA1UE
  <full certificate reduced to keep this example short>
  JBe9/l3FuXLjL0PpEdVaO7mlPceL1AlXU/pcnoSM
  -----END CERTIFICATE-----
```

Repeat for the key file (`key.pem`) and CA cert (`ca.pem`), to build a full set of tls properties:

```
helm.tls.enabled: "true"
helm.tls.cacert: |
  -----BEGIN CERTIFICATE-----
  MIIFxzCCA6+gAwIBAgIJANSZZeXuZLszMA0GCSqGSIb3DQEBCwUAMHoxCzAJBgNV
  BAYTAlVLMRMwEQYDVQQIDApTb21lLVN0YXRlMRAwDgYDVQQKDAdBY2NhbnRvMRAw
  <full certificate reduced to keep this example short>
  Z2T2275G1iqFkfbBPbOqNSlIhOxQgx3Mdq764L7kaASX7ElOjfyZS4Xssg==
  -----END CERTIFICATE-----
helm.tls.cert: |
  -----BEGIN CERTIFICATE-----
  MIIFWjCCA0ICCQD5Avb/OJ3QcTANBgkqhkiG9w0BAQsFADB6MQswCQYDVQQGEwJV
  SzETMBEGA1UECAwKU29tZS1TdGF0ZTEQMA4GA1UECgwHQWNjYW50bzEQMA4GA1UE
  <full certificate reduced to keep this example short>
  JBe9/l3FuXLjL0PpEdVaO7mlPceL1AlXU/pcnoSM
  -----END CERTIFICATE-----
helm.tls.key: |
  -----BEGIN RSA PRIVATE KEY-----
  MIIJKAIBAAKCAgEA3GJEBcZg7vTxIlZ9a2fKvi9FxJnn12GvhtvxfXdkdKwNmtds
  <full key reduced to keep this example short>
  sodtxV6twi+hKaLrv33pDGkfIyJM4tkLRzRYGIanRR+NdWFqS+/X9bSvmY8=
  -----END RSA PRIVATE KEY-----
```

# Complete Deployment Location Properties Example

YAML:
```yaml
driverNamespace: kubedriver
defaultObjectNamespace: default
clientConfig: |
  apiVersion: v1
  clusters:
  - cluster:
      certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUN5RENDQWJDZ0F3SUJBZ0lCQURBTkJna3Foa2lHOXcwQkFRc0ZBREFWTVJNd0VRWURWUVFERXdwcmRXSmwKY201bGRHVnpNQjRYRFRJd01EVXlOVEE1TXpJeE1Wb1hEVE13TURVeU16QTVNekl4TVZvd0ZURVRNQkVHQTFVRQpBeE1LYTNWaVpYSnVaWFJsY3pDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBTVB2CnZ0RkpvejllSndISTBGWkpHVHpadldtb0ZSYUxtbjdJMnFXVEVocFpkOHRMZzlvekY5OWdTekZSZUViU25mN0EKaUcyM2hOczJNWDFYL0hweXJDRVI2clRaME1GZE8zR1BUQ1dHZE9JaTNHa1BSS04zb1VFZkdKemM4SmxscmE2SAphck5NalV4dmhmZnEyVDFSdEVIcFlrOHlVd0M0U3RNbXkrTnhKelJ5RDQvbEZGU25LV1VYT21HZ2NsNm9YdDRPCnJvKzhMZ1RCMVhaOUg1NlNQUkU4dDFoMVk5eUNNaGdNTFJlREVvZlNDVWlaNk5idDVadUtqR1hod3Q1R1VrWVEKMUc4amxQNU53RmFVaVl4Y2d0L2dEVVk4eDJQR3ZuTjYrb2NQR0hwWXBHbDBQRGFjUk00VGUwZkxKOU9CSFZVZwp4NW1WQTJJRkFnZ2d5VkdWTFk4Q0F3RUFBYU1qTUNFd0RnWURWUjBQQVFIL0JBUURBZ0trTUE4R0ExVWRFd0VCCi93UUZNQU1CQWY4d0RRWUpLb1pJaHZjTkFRRUxCUUFEZ2dFQkFBNUpkR2oyVjMzVWExcDEyUzRwNmNyeXp4eC8KWmRER1lndmNsV0FZaTM3YWlvVzByVERwY2dHclkvZXpUVTBtUjVRbWY0MEJpZUk4NFZsVEJFUHR4VHlPR1IxbApXSk1YOVpvb3htYlBZVGIyQWwxRDYrYTNrejJwM0l2TFVFWmRtcE9BMjN2NVNjbmsvV281Vkw1NlV0VmFxSU9JCi9qWFNLMytqOVUrRGZBS1o5cXpyUVVLL2JreFNhRkN0SkIrK1cxVTJRd25PTVJ3YndFUmhSR1ZWa1BGeUlDbDAKSkpTOG9qOHp5OEtDVWZaeWliRTgwSDFVN2t4TjRNMTM0Z0ZyRlhlZ1d3NUlpbWtQMzhSVUVvUXZoQ0dBVXh5UQppMFZxa014MWhBQXA4SG1VdFE3WURRckpRQmk3UGpKTmJjRFJuMllxNmlCcVlXTFc0L3dtN1hQbHBEMD0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=
      server: https://203.0.113.254:6443
    name: kubernetes
  contexts:
  - context:
      cluster: kubernetes
      user: kubernetes-admin
    name: kubernetes-admin@kubernetes
  current-context: kubernetes-admin@kubernetes
  kind: Config
  preferences: {}
  users:
  - name: kubernetes-admin
    user:
      client-certificate-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUM4akNDQWRxZ0F3SUJBZ0lJS2hPQVdIdm4ybWt3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TURBMU1qVXdPVE15TVRGYUZ3MHlNVEExTWpVd09UTXlNVFZhTURReApGekFWQmdOVkJBb1REbk41YzNSbGJUcHRZWE4wWlhKek1Sa3dGd1lEVlFRREV4QnJkV0psY201bGRHVnpMV0ZrCmJXbHVNSUlCSWpBTkJna3Foa2lHOXcwQkFRRUZBQU9DQVE4QU1JSUJDZ0tDQVFFQXhVM2dyaURVelB6d21KNEQKSDdMZGtiM2p0VWg3d3dINzBzbGF2TW8xNS90bmxrMmRVc3lPc0wzMnJDL1lHWEd1eTJLK3FGYXJScTdrc25JWQpOTWdRc0hKOEVvemFiWmdhVjM5ZTJpcTR2SG9DQzgycVdib1BPaGJiRVBFNy9wZEtvbnlQUklpaTI4bi8zSFpSCkdjVzhibW1jOWxKdU94dmJJblNvV042R1lKSEdlTm1pSXcweVo0RnV0QXNhdVJMK1QzZGlRUFZ0MExiQXlYNWcKY0RhQkZRTFJnM0JxTzlnQk0yalVkc0NMbWtpV1hPTEFsb1RENVNsMW9rZFp0Z3NPMzhCVmM1Y0tJYXVQeUFBSgpLNkJTS0lraVRveXRlb3E1bnA1MDk0Tnp4aHU0ckdMa1lybnlXQWlyc05mbG9WdzZzcTRUZFVra2svcnExYzQvCmlUc3FRUUlEQVFBQm95Y3dKVEFPQmdOVkhROEJBZjhFQkFNQ0JhQXdFd1lEVlIwbEJBd3dDZ1lJS3dZQkJRVUgKQXdJd0RRWUpLb1pJaHZjTkFRRUxCUUFEZ2dFQkFKQkJnTXhCYzFhZ3ZSRjVOalpiWWp3bmthY01KK01idkdDTApQRU1iRXAzQzNrTFV1N0J0dUNYYjVIeURMdHhKc0ZmQnVTeE50WkYxT0NaSUYzYnk0ZTZmeWIvVjhaR0sxZmhhCnhicTRVd1FaNHkySUNoUk85KzFRR2tKM1dLK3dOTk1VaW9nakg3SEp5dlJKSG9oZ1JtMXNzY00yV1VkZ2oraksKa3I0S0ZpQVBtWTUxV1ZjZVloWWo2NlJaSkRQSUJ2L1hVeUpDRGxRMERPZ2c4bzN4eWNja1ZZTElEcGlZTWRTZAo1L3lLZEZNSHNHWEFwWE1ibUhwUnRmSytqdHh5enQ4Zm14c2lPRC9CVHZsQitsS2NtZ05UZ293eTZJQlhNQ1NMCjUwdFZhL1d3L2FOZE1aSjR6TFBKVXRoQ2taMTc2eElOVDBDNUdLVDgrb2RGNXJpcEhjQT0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=
      client-key-data: LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFcEFJQkFBS0NBUUVBeFUzZ3JpRFV6UHp3bUo0REg3TGRrYjNqdFVoN3d3SDcwc2xhdk1vMTUvdG5sazJkClVzeU9zTDMyckMvWUdYR3V5MksrcUZhclJxN2tzbklZTk1nUXNISjhFb3phYlpnYVYzOWUyaXE0dkhvQ0M4MnEKV2JvUE9oYmJFUEU3L3BkS29ueVBSSWlpMjhuLzNIWlJHY1c4Ym1tYzlsSnVPeHZiSW5Tb1dONkdZSkhHZU5taQpJdzB5WjRGdXRBc2F1UkwrVDNkaVFQVnQwTGJBeVg1Z2NEYUJGUUxSZzNCcU85Z0JNMmpVZHNDTG1raVdYT0xBCmxvVEQ1U2wxb2tkWnRnc08zOEJWYzVjS0lhdVB5QUFKSzZCU0tJa2lUb3l0ZW9xNW5wNTA5NE56eGh1NHJHTGsKWXJueVdBaXJzTmZsb1Z3NnNxNFRkVWtray9ycTFjNC9pVHNxUVFJREFRQUJBb0lCQUNIM0lDQ1p3a2h2bXJPTApNQnA2M2kzQ3RMcDJlZWUrSmEzSnYvY1VFR2VaSGVJQUJuOUVlNlB0YjlPQWdRRVFVdmpzVE1vSjhYNC9pVnMyCnpQZjVJUFpmSHdES2dxZXZNWW15Z1krcEh4aERJS3NMZ3JIamw4OTJNOHdjMnlrZXZsaHVmUE5kV2p2ZjhFM3gKaUZDWmU3QytPYWtsMDVnVldZbjY3eWd0VnBDMCtmdXhWd3Exd2IzazJGaG9wRWNSeDBKRE15cTNMVk1BZzlQLwpkbFlwSURCeVpadGx0K3A5SUhEdGpOcVk0MitFLzdCSVAvNy8xZHRSWE9MQllEWG1pd3ZERVVwM1pUeS9JSXJqCnJLL2tHTW5kTGFPZTM1SjU1Tjl2L1FCNUZJaFBXTUluNElPMWwrTGVNa3p2UzJBc2Z3UUNTbGRheVp4djVOWG4KNmFjTFlVa0NnWUVBOVNyVENUOHZFQ1JKQVZqS05FY3pOSDBEQTV6czJ2V1dhSEdPMnRHMFZOcGhKTGNEWk56OQphd1F3dXB4S3pYQ2lZYUttWTdhVzFFZ2NhZUtvbnRWNzNhRjNTUDhvdXFmbTdFMi9yNExiSTAzR1JXMkJpcTFVCk5aZFhQb09Sdkl6NFdMYnhrbTVsWU1qVXorZlQ0SlAxTjBLbzlsQVlQZHU0SVN4UzdSOGNaejhDZ1lFQXpnV28KSS93aEJFWGlkOXRNbDltR2c3UzREQmUvOWlYVUxOc2JGTU04R0ZEbW0rdk0xb2dWRzc0VSt2SGlCZ25mT1VneApNVWVWOTFqKzRkQVdlS0xHL2FNVGhQUmtnOENsaGN3ZG1PTGpCMnNmUlpwSUF2Vk1JZUhkSlJ0RUQ2L0ZBRm1oCnVrQnUvWGVsdmF2WUlOYVZkU2RKMEhVc2hjMGwyYnRZWTBaaGpuOENnWUVBck9IRDZ6Tlk5cUwvc0NseWZTYncKSHNWQXlOMXgwSDE1MExDek1lN0tvVU5WV1ZTTTJpVlR0cEUvNDNldTcrdkxOZHBDUnZKTXJla2owQzc3QlBZNQo0SEdwOGhtc0dPT3BYVnorSEwvRDA4TldXMEw3SkZWUm1uRGNIc01jazc4OHFTSm9ldi9LRVZQTmJjWm1qR2tKCmRDeFhoVW01cm5Vd0JJU0MvWjhBb25VQ2dZRUFwMmYzVVk0OU1lQ3JmaU1IWU5oVHNrKzF3YlhHdVBmU0tjUzgKZzZtRSttazZpZllZRXphdW1FVmpmT254ZEdDdkx6ZVhLV2oyMWU5TjVTV1dMTjV2L1lkMmcvR21mMXlaNDFlUgpzVHFqcWRLRXJhVUk0TVo3MzRoTmp5cFJxc0Z6dmE0WGVXV0VDcGdmYURqcnZQdEFwTnFRNHo5ak56SVVrSkRuCjZIczNLSGNDZ1lCbXNqRWdmZ3dtaExBT1hiZU9nbHBPVGNsdEo4bDgyUnlta2tpbHdBMUk4ancrQ0hZNUlYNzMKY3hTLzZ6eDk4VjVFY1JNVW43RUZYdUdCem5EcUJsMmVIbm96QzYxZk5Ldk5nL2Y1MEU2MEp5MnBBdFZPdklaYQptdlg1eUxWQVFOYTAvRnI5Y1ZtNmtQYXJRQ0t4aVFGaVRoUER5M2tmOStBbStzbnB3ekZYY1E9PQotLS0tLUVORCBSU0EgUFJJVkFURSBLRVktLS0tLQo=
helm.tls.enabled: True
helm.tls.cacert: |
  -----BEGIN CERTIFICATE-----
  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
  -----END CERTIFICATE-----
helm.tls.cert: |
  -----BEGIN CERTIFICATE-----
  MIIFWjCCA0ICCQD5Avb/OJ3QcTANBgkqhkiG9w0BAQsFADB6MQswCQYDVQQGEwJV
  SzETMBEGA1UECAwKU29tZS1TdGF0ZTEQMA4GA1UECgwHQWNjYW50bzEQMA4GA1UE
  CwwHQWNjYW50bzEPMA0GA1UEAwwGdGlsbGVyMSEwHwYJKoZIhvcNAQkBFhJ0aWxs
  ZXJAZXhhbXBsZS5jb20wHhcNMjAwNTI1MDkzOTQwWhcNMjEwNTI1MDkzOTQwWjBk
  MQswCQYDVQQGEwJVSzETMBEGA1UECAwKU29tZS1TdGF0ZTEUMBIGA1UECgwLaGVs
  bS1jbGllbnQxFDASBgNVBAsMC2hlbG0tY2xpZW50MRQwEgYDVQQDDAtoZWxtLWNs
  aWVudDCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBANxiRAXGYO708SJW
  fWtnyr4vRcSZ59dhr4bb8X13ZHSsDZrXbBGpvAHJBVHhnWmrJFwpYkOKaA+ek+Qz
  0VmTJsT5Nl/S/SfIpfwVhAzCu7yRcgtCYtRGq2D3FOm9kaGNawfhVTSNFPPKQugi
  0WWrw+uwnlpoyu4v2KDP/tq3mfa2i47obR0Fcv1cmEySIvez5w+gTffpZuFLGk5z
  ABwNl7H8k7yz47ROUYXTkj8MASee3yc6iJaTdmviJob+rQ1+3Tn17nYkLdQx6KCG
  3HUHWp6t+3GjIkAyAEhF1FrPPOrpQg/ss8kp1EINH0hrUcOxvz7/Mqy/8v/UYgq8
  HYCXVqZpxVjZ6R/Bf0YNqB2DVp14OqdjlRfHcbEnr81MJ95stiwgY2Qhprzp93Jx
  40QCL61eu9uJr47yatwmfpuwv13WpC6ZaBnP+5ZDlD/CoHWCLaKYrlqGOXZyEXHG
  eMI1+VTtWIoSsvrbpaeNGtGwjToYb5m+6LjOstIImKifumLVoO1R7vIyUSMOpUww
  hvtcqQ8TxzA4pX7fP31tBm1CWLzaXBnnNdVRq9gSp+/O0gs3iy6e2LlGFTDFqt7b
  ueZxoj306Q6SEqhWS/0fZPMake4zXTkK0o0CHZBgSv6ClnjgK/R8VB5T7PQ7coX4
  0WXfb9qMcUw7KOuI+Z8PzqwamHTRAgMBAAEwDQYJKoZIhvcNAQELBQADggIBAG8x
  POPst71TNyPdwG6E6y3Uaw4Pi3dPgmwEtqvCAODS/HLM67r0/zCgXiVtlHAn1hFD
  nuLtV0peaTt5m6tBRL8yzjHgn1maA+YBIXqKdDm9GnW/5ASLCbf1en4/+9QXxqGq
  8ZvEgCRikkJqJr7njlo3iMTpFvuOyTdCXZ1O3e8/Dema5+3w0L3qYqaRNp4lpasc
  XBweXUX9e1kluGbKgObIGOTkAKxo6bNMRio2HwhMcf/CFUU8YLBZN9BGn564Tlkx
  3VWRy/nOpWfhBtwWgAK9ghm0aETtiUexdDUPMaMlzinqTgE8m8z8SuPM+IIyj/T7
  Nj9zsGIVujT6/Uszym3odP6/KcDS15pg+0WukC3nXq09H2HAebYHV94Q4rFz0H5T
  VLsPmGWwIteHbXkpfgyqyX3UUnJurEWpMHCc1hyX/qazyLrTpLqljrgVpa7W19kQ
  JnlfyK/Dbnw34tPugWy1qsZU5HuPT1WtawCjUp6VFEqacHmbQ9TaDH1A+z2UKaUR
  NPvEDj3OOTK0jRNxlcYe7t7AgPu3dgrDqojCnh0s1s/VbgtdPNipeBVaEf/n4FFH
  9TQ1NvIs6+84zELWhG0q39soKUIh/fhuw28JYZ216xL6eYN7TquWeXAL2WjbDXiu
  JBe9/l3FuXLjL0PpEdVaO7mlPceL1AlXU/pcnoSM
  -----END CERTIFICATE-----
helm.tls.key: |
  -----BEGIN RSA PRIVATE KEY-----
  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
  -----END RSA PRIVATE KEY-----

```
