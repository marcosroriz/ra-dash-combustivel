var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.DMC_Button = function (props) {
    const {setData, data} = props;

    function onClick() {
        setData();
    }
    console.log("Left icon", props.leftIcon)
    console.log("Right icon", props.rightIcon)
    console.log("DASH ICONIFY", window.dash_iconify)
    
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

