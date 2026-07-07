# Microprocessor Trend Data

This repository contains the raw data used in my blog series on microprocessor trend data:

  * [50 Years of Microprocessor Trend Data](https://www.karlrupp.net/2018/02/42-years-of-microprocessor-trend-data/)
    ![50 Years of Microprocessor Trend Data Chart](https://github.com/karlrupp/microprocessor-trend-data/blob/master/50yrs/50-years-processor-trend.png?raw=true)
  * [48 Years of Microprocessor Trend Data](https://www.karlrupp.net/2018/02/42-years-of-microprocessor-trend-data/)
  * [42 Years of Microprocessor Trend Data](https://www.karlrupp.net/2018/02/42-years-of-microprocessor-trend-data/)
  * [40 Years of Microprocessor Trend Data](https://www.karlrupp.net/2015/06/40-years-of-microprocessor-trend-data/)

I have taken the liberty of keeping the data up to date thru 2026 and adding a few convenience features, since I wanted
to explore this data myself:

- Scripts to build output files
- Ability to ingest new data entered simply into the existing data format
- New HTML page for displaying the chart that is mouse interactive

## Local workflow

This fork includes a small local build workflow for inspecting the data and
re-rendering the existing gnuplot charts:

```bash
make check
make inspect
make interactive
make snapshot
make render
```

Edit `newdata.txt` as the human-readable source for newer processor rows.
`make interactive` builds a self-contained HTML file and standalone SVG under
`output/interactive/` with hover/focus details for named processor rows, without
modifying the historical gnuplot `.dat` files.
Rendered gnuplot outputs are copied to `output/rendered/`. The `patches/`
directory is for staging newer processor rows before appending them to
`newdata.txt`.

### License

All raw data and my own plots are available under a Creative Commons Attribution 4.0 International Public License, see file [LICENSE.txt](LICENSE.txt) for details.
