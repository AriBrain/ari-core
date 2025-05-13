

class HistogramCanvas(FigureCanvas):
    """ A Matplotlib canvas to display the histogram in the UI """
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(3, 1), dpi=100)  # Longer width than height
        
        # **Define self.ax to avoid errors later**
        self.ax = self.fig.add_subplot(111)

        super().__init__(self.fig)

        # **Set initial empty white background**
        self.ax.set_facecolor("white")  # White background on initialization
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["bottom"].set_visible(False)
        self.ax.spines["left"].set_visible(False)
        # self.ax.set_title("Waiting for Data...", fontsize=10, color="gray", fontweight="bold")
        # Center text
        self.ax.text(
            0.5, 0.5, "Waiting for Data...", 
            fontsize=12, color="gray", fontweight="bold",
            ha="center", va="center", transform=self.ax.transAxes  # Normalize to Axes (0-1 range)
        )

        self.fig.canvas.draw()


    def update_histogram(self, data):
        """ Update the histogram with new TDP values after ARI runs """

        self.ax.clear()  # Clear previous plot

        # Set a lighter background (default)
        self.ax.set_facecolor("#142735")  

        # Adjust axis and tick colors
        self.ax.spines["bottom"].set_color("white")
        self.ax.spines["left"].set_color("white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.tick_params(colors="white", labelsize=8)  # Increased label size

        # **Set Title**
        # self.ax.set_title("TDP Distribution", fontsize=10, color="white", fontweight="bold")

        # **Plot Histogram with Pastel Red Bars**
        counts, bins, patches = self.ax.hist(data, bins=75, color="#ff9999", edgecolor="black", alpha=0.85)

         # Get max frequency from histogram
        hist_max = max(counts)  

        # Compute KDE values
        kde = sns.kdeplot(data, ax=self.ax, color="black", bw_adjust=0.5)

        # Extract KDE x and y data
        kde_lines = kde.get_lines()[0]  # Get the KDE line object
        x_kde, y_kde = kde_lines.get_xdata(), kde_lines.get_ydata() 

        # **Scale KDE Y-data to histogram max height**
        y_kde_scaled = y_kde * hist_max / max(y_kde)

        # Plot scaled KDE curve
        self.ax.plot(x_kde, y_kde_scaled, color="black", linewidth=1.5)

        # # **Theoretical Normal Fit**
        # mu, sigma = np.mean(data), np.std(data)  # Compute mean and std
        # x = np.linspace(min(data), max(data), 300)  # X-axis range
        # normal_dist = stats.norm.pdf(x, mu, sigma)  # Compute normal distribution

        # # **Scale normal curve to histogram**
        # normal_dist *= max(counts) / max(normal_dist)

        # # **Plot Normal Fit as Dashed Yellow**
        # self.ax.plot(x, normal_dist, linestyle="dashed", color="yellow", linewidth=1.5, label="Normal Fit")


        # Compute KDE
        kde = stats.gaussian_kde(np.array(data), bw_method=0.4)

        # Generate x values for plotting
        x = np.linspace(min(data), max(data), 300)  # X-axis from min to max TDP

        # Compute KDE values for x-axis
        kde_values = kde(x)
        kde_values *= max(counts) / max(kde_values)

        # Plot KDE
        self.ax.plot(x, kde_values, linestyle="dashed", color="yellow", linewidth=1.5) 

        # **Set X-Ticks at 0, 0.5, and 1**
        self.ax.set_xticks([0, 0.5, 1.0])
        self.ax.set_xticklabels(["0", "0.5", "1.0"], fontsize=6, color="white")

        # **Scale Y-Axis by 1000**
        self.ax.set_yticks(np.arange(0, max(counts) + 10000, 10000))
        self.ax.set_yticklabels([str(int(y / 1000)) for y in self.ax.get_yticks()], fontsize=6, color="white")
        # self.ax.set_ylabel("Freq. (x1000)", fontsize=8, color="white", fontweight="bold")

        # **Adjust Labels**
        self.ax.set_xlabel("TDPs", fontsize=8, color="white", fontweight="bold")

        # **Make the graph take up more space**
        self.ax.set_position([0.00, 0.00, 1, 1])  # Adjust margins (left, bottom, width, height)

        # Redraw canvas
        self.fig.canvas.draw()