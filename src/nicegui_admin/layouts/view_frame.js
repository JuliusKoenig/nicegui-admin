export default {
    template: "<div><slot></slot></div>",
    mounted() {
        // ToDo: reload content from server if history changed (back/forward)

        // // create open event listener
        // window.addEventListener("popstate", (event) => {
        //     if (event.state?.page) {
        //         this.$emit("open", event.state.page);
        //     }
        // });
        //
        // // set connect interval
        // const connectInterval = setInterval(async () => {
        //     // if socket not connected yet, return
        //     if (window.socket.id === undefined) return;
        //
        //     // emit open event with current view path
        //     console.log("open", window.location);
        //     this.$emit("open", window.location.pathname + window.location.search);
        //     clearInterval(connectInterval);
        // }, 10);
    },
    props: {},
};