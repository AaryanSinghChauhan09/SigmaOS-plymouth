    # SigmaOS-plymouth

    Boot splash / plymouth theme manager

    Part of the **SigmaOS** sovereign operating-system ecosystem — a multi-repository
    distribution modelled on Linux Mint and Omarchy Linux. See the parent
    [`SigmaOS`](https://github.com/AaryanSinghChauhan09/SigmaOS) repository for the
    full component index.

    ## Upstream inspirations
    - https://github.com/linuxmint/plymouth

    ## Design principles applied
    - **Pure Plan / Thin Execute**
- **Fail-Fast**
- **Deterministic Testing**
- **KISS**
- **DRY**

    ## Usage
    Verbs: `themes, set, preview, build`

    ```
    $ sigma-plymouth themes
$ sigma-plymouth set sigma-dark --config ./plymouthd.conf
$ sigma-plymouth preview sigma-dark --width 48 --frame 3
$ sigma-plymouth build ./theme-src --name sigma-aurora

    ```

    ## Build & test
    ```
    make build
    make test
    ```

    ## Licence
    GNU General Public License v3.0 (FOSS).
