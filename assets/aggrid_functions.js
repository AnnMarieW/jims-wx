var dagcomponentfuncs = (window.dashAgGridComponentFunctions =
    window.dashAgGridComponentFunctions || {});

dagcomponentfuncs.ColorCellRenderer = (props) => {

    const colors = {
        VFR: '#0CC502',
        MVFR: '#226ED8',
        IFR: '#FF2700',
        LIFR: '#FF40FF',
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
        width: 18,
        height: 18,
        backgroundColor: color,
    };

    return React.createElement("div", {}, [
        React.createElement("span", { style: styles }),
    ]);
};