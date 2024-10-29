import pandas as pd
from process_data import aggregate, district_names, countyAggregate
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# Load data and compute static values
from shiny import App, reactive, render, ui


# rsconnect deploy shiny "C:\Users\joliphant\OneDrive - El Dorado County Office of
# Education\Documents\shinyPractice\upp_dashboard" --name edcoe-fiscal-data --title
# unduplicatedpercentage


districts = list(district_names.values())

# Add page title and sidebar
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.card(
            ui.input_checkbox_group(
                "districts",
                "Districts to Display",
                districts,
                selected=districts,
                inline=False,
            ),
            ui.div(
                ui.input_action_button(
                    "selectAll", "Select All", class_="small-button"
                ),
                ui.input_action_button(
                    "selectNone", "Select None", class_="small-button"
                ),
                style="display: flex; justify-content: space-between; gap: 10px;",
            ),
        ),
        ui.card(
            ui.input_checkbox(
                "charter",
                "Include Charter?",
                value=True,
            ),
            ui.input_checkbox(
                "normalize",
                "Normalize Enrollment Counts?",
                value=True,
            ),
        ),
        ui.card_footer("'24-25 data updated 10/29/2024"),
        ui.tags.style(
            """
        .small-button {
            font-size: 1em;
            padding: 4px 8px;
        }
    """
        ),
        width="300px" ,
        open="desktop",
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header(
                ui.h5(ui.output_text("header_text")),
            ),
            ui.output_plot("upp_plot"),
            full_screen=True,
        ),
        ui.card(
            ui.card_header(
                ui.h5("Unduplicated Pupil Percentage"),
            ),
            ui.output_plot("upp_plot2"),
            full_screen=True,
        ),
    ),
    title="El Dorado County UPP",
    fillable=True,
)


def server(input, output, session):

    @output
    @render.text
    def header_text():
        if input.normalize():
            return "Normalized Enrollment Counts (if your district had 100 students in 2016)"
        return "Enrollment Counts"

    @render.plot
    def upp_plot():
        input_districts = list(input.districts())
        if not input_districts:
            return
        fig, ax = plt.subplots()

        if not input.charter():
            plotdata = aggregate.query("charter == False")
            plotCounty = countyAggregate.query("charter == False")
        else:
            plotdata = aggregate
            plotCounty = countyAggregate

        plotdata_df = (
            plotdata.query("LEA.isin(@input_districts)")
            .groupby(["YEAR", "LEA"])
            .enrollment.sum()
            .unstack()
        )
        plotCounty_df = plotCounty.groupby("YEAR").countyEnroll.sum()
        plotCountyNormalized = plotCounty_df.mul(100).div(plotCounty_df.iloc[0])

        if input.normalize():
            plotdata_normalized = 100 * plotdata_df.div(plotdata_df.iloc[0, :])
        else:
            plotdata_normalized = plotdata_df

        final_plotdata = plotdata_normalized.sort_values(
            plotdata_normalized.last_valid_index(), axis=1, ascending=False
        )

        final_plotdata.plot(
            ax=ax,
            linewidth=3,
            style=["-o", "-^", "-s", "->", "--o", "--^", "--s", "-->"] * 4,
        )

        if input.normalize():
            ax.plot(
                plotCountyNormalized.index.to_list(),
                plotCountyNormalized.to_list(),
                "k:",
            )

        for i, v in enumerate(final_plotdata.iloc[-1, :]):
            ax.text(
                len(final_plotdata) - 1 + 0.3 * (i % 2),
                v,
                f"{v:.0f}",
                fontdict={"fontsize": "10"},
            )

        ax.grid(True)
        plt.legend(bbox_to_anchor=(0.5, -0.25), loc="lower center", ncol=4)

    @render.plot
    def upp_plot2():
        input_districts = list(input.districts())
        if not input_districts:
            return
        fig, ax = plt.subplots()

        if input.charter():
            plotdata = (
                aggregate.query("LEA.isin(@input_districts)")
                .groupby(["YEAR", "LEA"])
                .sum()
                .assign(UPP=lambda df_: df_.undupMealEng / df_.enrollment)
                .UPP.unstack()
            )
            plotCounty = (
                countyAggregate.groupby("YEAR")
                .sum()
                .assign(UPP=lambda df_: df_.countyUndupMealEng / df_.countyEnroll)
            )
        else:
            plotdata = (
                aggregate.query("LEA.isin(@input_districts)")
                .query("charter==False")
                .groupby(["YEAR", "LEA"])
                .sum()
                .assign(UPP=lambda df_: df_.undupMealEng / df_.enrollment)
                .UPP.unstack()
            )
            plotCounty = (
                countyAggregate.query("charter==False")
                .groupby("YEAR")
                .sum()
                .assign(UPP=lambda df_: df_.countyUndupMealEng / df_.countyEnroll)
            )
        final_plotdata = plotdata.sort_values(
            plotdata.last_valid_index(), axis=1, ascending=False
        )
        final_plotdata.plot(
            ax=ax,
            linewidth=3,
            style=["-o", "-^", "-s", "->", "--o", "--^", "--s", "-->"] * 4,
        )
        ax.plot(plotCounty.index.to_list(), plotCounty.UPP.to_list(), "k:")
        xlims = ax.get_xlim()
        ax.plot(xlims, [0.55, 0.55], "k:")
        ax.set_xlim(xlims)

        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, 0))

        for i, v in enumerate(final_plotdata.iloc[-1, :]):
            ax.text(
                len(final_plotdata) - 1 + 0.3 * (i % 2),
                v,
                f"{v:.0%}",
                fontdict={"fontsize": "10"},
            )

        ax.grid(True)
        plt.legend(bbox_to_anchor=(0.5, -0.25), loc="lower center", ncol=4)

    @reactive.effect
    @reactive.event(input.selectAll)
    def _():
        ui.update_checkbox_group("districts", selected=districts)

    @reactive.effect
    @reactive.event(input.selectNone)
    def _():
        ui.update_checkbox_group("districts", selected=[])


app = App(app_ui, server)
