# Contribution guidelines

## Code Practices

**Line Length** FIDS does not adhere to PEP8 line recommendations of 79 characters, instead just requires it fitting on 1080 at 12px font-size (less than 90 characters); roughly 84 characters is appreciated as this fits perfectly in VSCode. 

**Line Wrapping** Since FIDS uses a lot of HTML, CSS, and JS components, a unified syntax is used where arguments are encouraged to be split on new line with C guidelines. 

**Speed over clarity** Preference is given to performance of code over the clarity in which it is written, within reason of course. 

**Clear documentation** Following of the previous statement, clear descriptions of what exactly a function does are encouraged, and to keep comments of pitfalls that are rather unexpected but negatively affect performance. 

**If possible, generalize** Addition should be useful for the broadest possible audience.

**Dynamic is better than static** Allow scaling to any number of columns, axes, datasets, etc. with as few parameters as possible.

**Minimal pre-processing** Lazy computations and loading is preferred to allow quick initializations to peak into new datasets.
