# Templating

Templating is used to allow properties of a Resource to be injected into files, as a way of dynamically configuring the contents of files used by the Kubernetes driver on a request.

There are various files in an Kubernetes driver based Resource which support templated values. Generally, templating is either supported:

- as full template files - template syntax can be used anywhere in a file, it is rendered before it is parsed
- as templated YAML values, where they are rendered individually as single strings

This section describes the difference, how properties can be injected and the possible property values. It is important to understand how this works so you may build configurable templates which make use of the values passed down by the Lifecycle Manager (ALM).

# Template Syntax

This driver uses the [Jinja2 template syntax](https://jinja.palletsprojects.com/en/2.10.x/templates) to inject property values from the resource:

Example template syntax to inject value of property "dataA":
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: example-a
data:
  dataA: {{ dataA }}
  dataB: valueB
```

You may also use [control structures](https://jinja.palletsprojects.com/en/2.11.x/templates/#if) to configure optional elements of the object:

Example template syntax for conditional block based on the "protocol" property value:
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: example-a
data:
{% if protocol == 'https' -%}
  port: 443
  ssl: true
{% elif protocol == 'http' -%}
  port: 80
  ssl: false
{% else -%}
  customProtocol: {{ protocol }}
  ssl: false
{-% endif %}
```

We'll cover the full list of valid properties which may be used in templates later, in [Available Properties](properties.md).

# Full Template Files

Some files are full templates, meaning they are rendered first (so property values are injected) before they are parsed and expected to be valid. 

For example, this YAML file cannot be parsed:

```
someKey: someValue
anotherKey: {{ myInjectedProperty }}
```

It makes use of a templated value (myInjectedProperty, we'll cover the syntax in more detail later) so it must be rendered first to produce valid YAML. Let's assume there is a property named `myInjectedProperty` with a value of `abc`. After rendering the above template, expect it's contents to be:

```
someKey: someValue
anotherKey: abc
```

Now it is valid YAML and can be parsed without error.

Examples of full template files, used by the Kubernetes driver, include:

- object configuration files (kept in the `objects` directory of the resource package `Lifecycle/kubernetes` directory)
- helm values files (kept in the `helm` directory of the resource package `Lifecycle/kubernetes` directory)

# Templated YAML values

In the `kegd.yaml` file (at the root of the resource package `Lifecycle/kubernetes` directory), you cannot use templated values freely in the file. Instead, some of the fields in this file support referencing templated values. 

For example, when deploying objects, you may template the name of the file to use:

```
compose:
  - name: Create
    deploy:
      - objects:
          file: "{{ fileToUse }}"
```

You'll notice in this case, the templated value is surrounded by quotes. This is because the file will be parsed as YAML before the rendering takes place, so if a value starts with a templated value it must be quoted. 

If it's not used at the start, it doesn't need quotes. For example:

```
compose:
  - name: Create
    deploy:
      - objects:
          file: my-{{ fileToUse }}
```

When the Create transition is executed, the value of file is rendered individually. As in, a single string based template is provided with just the value:

```
my-{{ fileToUse }}
```

This is rendered to a resulting string which is used as the real value. So assuming there is a property named `fileToUse` with a value of `deployment.yaml`. After rendering the above template, expect it's contents to be:

```
my-deployment.yaml
```

Now the value of `file` in the parsed result of the kegd.yaml file is `my-deployment.yaml`. 

To clarify, the following is not allowed in the `kegd.yaml` file:

```
compose:
  - name: Create
    deploy:
      - objects:
{% if fileToUse == 'deployment' %}
          file: my-deployment.yaml
{% else %}
          file: my-other-file.yaml
{% end %}
```

This is not valid YAML and will never be rendered as a full template, so never will be.

# Next Steps

Check out the full range of [available properties](properties.md)