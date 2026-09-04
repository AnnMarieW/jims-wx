var dagcomponentfuncs = (window.dashAgGridComponentFunctions =
    window.dashAgGridComponentFunctions || {});

dagcomponentfuncs.ColorCellRenderer = (props) => {

    const colors = {
        VFR: "green",
        MVFR: "blue",
        IFR: "red",
        LIFR: "magenta",
    };

    const value = props.value?.toUpperCase();
    const color = colors[value];

    if (!color) {
        return null;
    }

    const styles = {
        verticalAlign: "middle",
        border: "1px solid black",
        borderRadius: "50%",
        margin: 3,
        display: "inline-block",
        width: 12,
        height: 12,
        backgroundColor: color,
    };

    return React.createElement("div", {}, [
        React.createElement("span", { style: styles }),
    ]);
};