# DocString Formatting Guide

This guide defines the standard conventions for creating Python DocStrings in the `Instruments_Libraries` module. The project uses Sphinx with the `sphinx.ext.napoleon` (Numpydoc) parser. 

Adhering to these rules ensures that the Sphinx HTML documentation renders beautifully and consistently without unnecessary line breaks or layout issues.

## 1. General Structure (Numpydoc)
Use the standard Numpydoc format. Only include a `Returns` section if the function actually returns a specific object other than `None`.

```python
def set_output_state(self, state: str | int) -> None:
    """
    Sets the general output state of the instrument.

    Parameters
    ----------
    state : str | int
        State of the output. Default: ``'ON'``.

        * ``'ON'`` / ``1`` : Activates the output.
        * ``'OFF'`` / ``0`` : Deactivates the output.
    """
    ...
```

## 2. Formatting Rules for Parameters

### Inline Text Alignment inside Parameters
When defining a parameter, its short description should immediately follow on the next line (indented by 4 spaces or 1 tab stop relative to the parameter name). 
**DO NOT use an empty line before the description or between the description and any subsequent bulleted lists.** Doing so breaks the Numpydoc parsing engine or creates awkward HTML layouts.

**Correct:**
```python
    state : str | int
        State of the output. Default: ``'ON'``.

        * ``'ON'`` / ``1`` : Activates the output.
```

**Incorrect:**
```python
    state : str | int

        State of the output. Default: ``'ON'``.
        
        * ``'ON'`` / ``1`` : Activates the output.
```

### Inline Code Highlighting
Use double backticks (`` ` ` ``) to format parameter options, numbers, and strings so they display as highlighted code blocks in the documentation. String literals must include quotes inside the backticks.
* String literal: `` `'ON'` ``
* Integer/Float: `` `1` ``, `` `42.5` ``
* Specific variables: `` `value` ``

### Formats for "Default"
If a parameter has a default behavior, indicate it at the end of the short description sentence in a consistent format: `Default: ``value```.

*Example:* `The phase modulation mode. Default: ``'MIN'``.`

### Formats for "Range"
When explaining the valid numerical bounds of a parameter, use bullet points with a bold **Range:** prefix.

*Example:*
```python
    value : int | float
        Continuous Wave Frequency. Default: ``10 MHz``.

        * **Range**: ``10 MHz`` to ``40 GHz``
```

### Formats for "Valid options" and "Units"
When listing out a short finite set of valid string choices (like units or simple ON/OFF states), use the phrase `Valid options:` followed by a comma-separated list of the options inside inline code blocks.

*Example:*
```python
    unit : str
        Frequency unit. Valid options: ``'Hz'``, ``'kHz'``, ``'MHz'``, ``'GHz'``.
```

For parameters with a short list of specific configurations where the meaning of the options is not immediately obvious (e.g., abbreviations like ``'CV'``, ``'CC'``, ``'CR'``), use a bulleted list to explain each option:

*Example:*
```python
    mode : str
        Select Load mode.

        * ``'CV'`` : Constant Voltage
        * ``'CC'`` : Constant Current
        * ``'CR'`` : Constant Resistance
```

For parameters with a short list of specific configurations, use bullet points without bold text if explaining the option:
```python
    state : str | int
        Output state. Default: ``'ON'``.

        * ``'ON'`` / ``1`` : Activates the RF output.
        * ``'OFF'`` / ``0`` : Deactivates the RF output.
```

## 3. Standard Units
Always prefer the standard SI base unit representation across the library where applicable. Do not write full words for standard units unless it adds critical context.
* **Frequency:** Hz, kHz, MHz, GHz
* **Time:** s, ms, us, ns
* **Power:** dBm, W, mW
* **Voltage:** V, mV
* **Ratio:** dB

*(Note: In Python function signatures, it is heavily recommended to use `'Hz'`, `'s'`, `'dBm'`, etc., as default string arguments where applicable to make intention clear.)*
