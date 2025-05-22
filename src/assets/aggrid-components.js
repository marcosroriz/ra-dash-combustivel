// assets/aggrid-components.js

var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.MultiButtonRenderer = function (props) {
    let items = [];

    try {
        let trips = props.value;
        if (typeof trips === "string") {
            trips = JSON.parse(trips);
        }

        const vehicleId = props.data.vehicle_id;

        items = trips.map((trip, idx) =>
            React.createElement(
                "button",
                {
                    key: idx,
                    type: "button",
                    className: "btn btn-sm btn-" + trip.color + " me-1",
                    "data-value": trip.value,
                    "data-vehicle-id": vehicleId,
                    onclick: (e) => {
                        // Trigger AG Grid's cellClicked event manually
                        if (props.api) {
                            props.api.dispatchEvent({
                                type: 'cellClicked',
                                data: props.data,
                                colDef: props.colDef,
                                event: e
                            });
                        }
                    }
                },
                `${trip.value} km/l`
            )
        );
    } catch (e) {
        items = [React.createElement("span", {}, "invalid format")];
    }

    return React.createElement("div", {}, items);
};
