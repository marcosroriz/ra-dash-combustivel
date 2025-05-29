var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.DMC_Viagens = function (props) {
    const { setData, data } = props;

    function onClick() {
        setData();
    }

    let items = [];
    let trips = typeof props.data.trips === "string" ? JSON.parse(props.data.trips) : props.data.trips;

    // Adiciona cada trip
    items = trips.map((t, ix) => {
        // Cria o label
        label = `${t.value} km/L LINHA (${t.linha})`

        // Cria o ícone
        icone = "mdi:check-bold"
        if (t.color == "warning") {
            icone = "mdi:warning"
        } else if (t.color == "danger") {
            icone = "mdi:dangerous"
        }

        reactIcone = React.createElement(window.dash_iconify.DashIconify, {
            icon: icone,
            width: 32
        });

        // Cores
        cor = "green"
        if (t.color == "warning") {
            cor = "orange"
        } else if (t.color == "danger") {
            cor = "red"
        }

        return React.createElement(
            window.dash_mantine_components.Button,
            {
                onClick,
                color: cor,
                // leftSection: reactIcone,
                radius: props.radius,
                style: {
                    marginRight: "8px",
                    marginBottom: "4px",

                    // margin: props.margin,
                    // display: 'flex',
                    // justifyContent: 'center',
                    // alignItems: 'center',
                },
            },
            label
        )
    })

    return React.createElement("div", {}, items);
}

dagcomponentfuncs.DMC_Button = function (props) {
    const { setData, data } = props;

    function onClick() {
        setData();
    }
    console.log("Left icon", props.leftIcon)
    console.log("Right icon", props.rightIcon)
    console.log("DASH ICONIFY", window.dash_iconify)
    console.log("VALUE", props.value)
    console.log("_--------")
    let leftIcon, rightIcon;
    if (props.leftIcon) {
        leftIcon = React.createElement(window.dash_iconify.DashIconify, {
            icon: props.leftIcon,
        });
    }
    if (props.rightIcon) {
        rightIcon = React.createElement(window.dash_iconify.DashIconify, {
            icon: props.rightIcon,
            width: 32
        });
    }
    return React.createElement(
        window.dash_mantine_components.Button,
        {
            onClick,
            variant: props.variant,
            color: props.color,
            leftSection: leftIcon,
            leftIcon,
            rightIcon,
            radius: props.radius,
            style: {
                margin: props.margin,
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
            },
        },
        props.value
    );
};

