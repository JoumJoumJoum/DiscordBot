import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Embedded tournament data
POINTS_DATA = {
    "225169014375055360": {
        "username": "apaar50",
        "points_history": [
            0, 2, 7, 7, 7, 7, 7, 8, 8, 9, 9, 9, 10, 10, 10, 10, 14, 15, 16, 17, 19, 19, 22, 22, 22, 28, 33, 33, 33, 33, 33, 34, 34, 36, 37, 37, 39, 40, 45, 50, 50, 51, 52, 52, 52, 53, 53, 53, 53, 53, 53, 54, 55, 55, 55, 55, 55, 56, 56, 56, 56, 58, 60, 61, 61, 62, 67, 68, 70, 70, 73, 74, 74, 74, 75, 75, 75, 76, 77, 80, 81, 84, 85, 86, 87, 87, 89, 90, 91, 93, 94, 94, 94, 95, 97, 98, 103, 104, 106, 109, 110, 110, 118, 118, 118
        ]
    },
    "852765605814992956": {
        "username": "miltonthermo",
        "points_history": [
            0, 2, 7, 12, 15, 15, 15, 16, 16, 17, 17, 17, 17, 17, 17, 17, 17, 18, 19, 20, 22, 22, 22, 22, 25, 25, 25, 27, 27, 31, 31, 32, 32, 34, 35, 35, 37, 38, 38, 38, 38, 39, 40, 43, 46, 47, 47, 50, 52, 56, 57, 58, 59, 61, 61, 61, 64, 65, 65, 65, 70, 70, 72, 73, 73, 74, 74, 75, 77, 77, 77, 78, 78, 81, 81, 81, 81, 82, 83, 83, 84, 87, 88, 89, 90, 94, 94, 95, 96, 98, 99, 103, 104, 104, 106, 107, 107, 108, 108, 108, 108, 116, 116, 124, 136
        ]
    },
    "310433679342043136": {
        "username": "Joum",
        "points_history": [
            0, 2, 2, 2, 2, 2, 9, 9, 9, 9, 9, 9, 10, 10, 16, 21, 21, 22, 22, 23, 23, 23, 26, 26, 29, 29, 29, 31, 31, 31, 31, 32, 32, 32, 32, 32, 32, 32, 32, 37, 37, 38, 38, 38, 41, 41, 41, 41, 41, 41, 42, 43, 44, 46, 46, 46, 46, 47, 47, 47, 47, 47, 49, 49, 55, 56, 56, 56, 56, 60, 60, 61, 61, 64, 65, 65, 65, 66, 67, 70, 71, 71, 72, 73, 73, 77, 79, 80, 80, 80, 81, 81, 82, 83, 85, 86, 86, 86, 86, 86, 87, 95, 95, 103, 115
        ]
    },
    "768080288009158706": {
        "username": "Alankr\u03c0",
        "points_history": [
            0, 2, 2, 7, 10, 10, 10, 11, 11, 12, 16, 16, 17, 17, 17, 17, 17, 18, 19, 20, 22, 22, 25, 29, 32, 32, 37, 39, 44, 48, 51, 52, 52, 52, 53, 53, 55, 56, 56, 56, 61, 62, 63, 63, 66, 67, 67, 70, 72, 76, 77, 78, 79, 81, 81, 81, 84, 85, 85, 85, 85, 87, 89, 90, 90, 91, 91, 92, 94, 98, 101, 102, 107, 110, 111, 111, 116, 117, 118, 121, 122, 122, 123, 124, 125, 125, 127, 128, 129, 131, 132, 132, 133, 134, 134, 135, 135, 136, 138, 141, 142, 142, 150, 150, 162
        ]
    },
    "155298026796220416": {
        "username": "blacroc",
        "points_history": [
            0, 2, 2, 2, 5, 12, 12, 13, 13, 14, 18, 18, 18, 18, 18, 18, 18, 19, 20, 21, 23, 23, 23, 23, 26, 26, 26, 28, 33, 37, 40, 41, 41, 43, 44, 44, 46, 47, 47, 47, 52, 53, 54, 57, 57, 58, 58, 61, 63, 67, 68, 69, 70, 72, 72, 72, 72, 73, 73, 73, 73, 75, 77, 77, 77, 77, 77, 78, 78, 82, 82, 83, 88, 88, 89, 89, 89, 90, 91, 91, 92, 95, 95, 96, 97, 97, 99, 100, 101, 103, 104, 108, 109, 110, 112, 113, 113, 114, 116, 119, 120, 128, 128, 128, 128
        ]
    },
    "779019518357405726": {
        "username": "raykonik",
        "points_history": [
            0, 0, 0, 0, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 7, 8, 8, 8, 9, 9, 9, 10, 10, 15, 15, 16, 17, 20, 23, 24, 24, 24, 26, 26, 27, 27, 28, 28, 28, 28, 28, 28, 28, 28, 28, 30, 30, 31, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 49
        ]
    },
    "464295598497988640": {
        "username": "homeless",
        "points_history": [
            0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 6, 11, 12, 12, 12, 12, 16, 17, 18, 19, 19, 19, 19, 23, 23, 29, 29, 31, 31, 31, 34, 35, 35, 37, 38, 45, 47, 48, 53, 53, 58, 59, 60, 63, 63, 64, 64, 67, 69, 69, 70, 71, 72, 74, 74, 74, 77, 78, 78, 78, 83, 85, 87, 88, 88, 89, 94, 95, 97, 97, 100, 101, 101, 104, 105, 105, 110, 111, 112, 112, 113, 113, 114, 115, 116, 116, 118, 119, 120, 122, 123, 127, 127, 128, 130, 131, 131, 132, 134, 137, 138, 138, 138, 146, 146
        ]
    },
    "750366001580998678": {
        "username": "Dhruv\ud83d\udc99",
        "points_history": [
            0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 7, 8, 8, 8, 13, 17, 18, 19, 20, 22, 22, 25, 29, 29, 29, 34, 34, 34, 38, 38, 38, 45, 45, 46, 46, 48, 49, 49, 49, 49, 50, 51, 54, 54, 55, 55, 58, 60, 64, 65, 66, 67, 69, 69, 69, 72, 72, 72, 78, 78, 80, 80, 81, 81, 82, 82, 83, 85, 85, 88, 89, 89, 89, 90, 90, 90, 90, 91, 94, 95, 98, 99, 100, 101, 105, 105, 106, 107, 107, 108, 108, 109, 110, 110, 111, 116, 117, 119, 119, 120, 120, 128, 128, 128
        ]
    }
}

def sanitize_username(username):
    # Remove emojis and non-ascii characters to prevent Matplotlib font errors
    return "".join(c for c in username if ord(c) < 128 or c == '\u03c0')

def main():
    # Sanitize all usernames
    for uid, udata in POINTS_DATA.items():
        udata["username"] = sanitize_username(udata["username"])

    max_len = max(len(u["points_history"]) for u in POINTS_DATA.values())
    max_pts = max(max(u["points_history"]) for u in POINTS_DATA.values())

    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    bg = "#1A1B26"
    grid = "#2D3142"
    text = "#A9B1D6"

    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    colors = [
        "#FF2E93", "#00F0FF", "#4ADE80", "#FBBF24", 
        "#A855F7", "#F97316", "#EC4899", "#3B82F6",
        "#14B8A6", "#EF4444"
    ]
    user_colors = {}
    for idx, uid in enumerate(POINTS_DATA.keys()):
        user_colors[uid] = colors[idx % len(colors)]

    lines = {}
    for uid, udata in POINTS_DATA.items():
        line, = ax.plot([], [], label=udata["username"], color=user_colors[uid], linewidth=2.5)
        lines[uid] = line

    ax.set_xlim(0, max_len - 1)
    ax.set_ylim(0, max_pts + 5)

    ax.grid(True, color=grid, alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(grid)
    ax.spines["bottom"].set_color(grid)
    ax.tick_params(colors=text)
    ax.set_xlabel("Match Days / Predictions", color=text, fontsize=12)
    ax.set_ylabel("Points Earned", color=text, fontsize=12)
    
    ax.text(
        0.01,
        1.05,
        "🏆 World Cup Predictions Race Standings",
        transform=ax.transAxes,
        color=text,
        fontsize=14,
        fontweight="bold",
        ha="left"
    )

    ax.legend(
        facecolor=bg,
        edgecolor=grid,
        labelcolor=text,
        loc="upper left",
        ncol=2
    )

    plt.tight_layout()

    def init():
        for line in lines.values():
            line.set_data([], [])
        return list(lines.values())

    def update(frame):
        for uid, udata in POINTS_DATA.items():
            hist = udata["points_history"]
            x = list(range(min(frame + 1, len(hist))))
            y = hist[:frame + 1]
            lines[uid].set_data(x, y)
        return list(lines.values())

    ani = animation.FuncAnimation(
        fig, update, frames=max_len, init_func=init, blit=True, interval=150
    )

    output_mp4 = "points_race.mp4"
    output_gif = "points_race.gif"

    print("Compiling animation...")
    
    # Try saving as MP4 first (requires ffmpeg)
    try:
        print("Attempting to save as MP4 video...")
        ani.save(output_mp4, writer="ffmpeg", fps=6)
        print(f"Success! MP4 video saved to: {output_mp4}")
    except Exception as e_mp4:
        print(f"Could not save as MP4 (FFmpeg might not be installed): {e_mp4}")
        # Fallback to GIF (does not require external tools, uses pillow)
        try:
            print("Falling back and saving as GIF animation...")
            ani.save(output_gif, writer="pillow", fps=6)
            print(f"Success! GIF animation saved to: {output_gif}")
        except Exception as e_gif:
            print(f"Error saving GIF: {e_gif}")

if __name__ == "__main__":
    main()
